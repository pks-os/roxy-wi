import os

from flask import render_template

import app.modules.db.sql as sql
import app.modules.db.cred as cred_sql
import app.modules.db.backup as backup_sql
import app.modules.db.server as server_sql
import app.modules.db.service as service_sql
import app.modules.server.ssh as ssh_mod
import app.modules.server.server as server_mod
import app.modules.roxywi.common as roxywi_common
import app.modules.service.installation as installation_mod


def backup(serv, rpath, time, backup_type, rserver, cred, deljob, update, description) -> str:
    script = 'backup.sh'
    ssh_settings = ssh_mod.return_ssh_keys_path(rserver, id=cred)
    full_path = '/var/www/haproxy-wi/app'

    if deljob:
        time = ''
        rpath = ''
        backup_type = ''
    elif update:
        deljob = ''
    else:
        deljob = ''
        if backup_sql.check_exists_backup(serv):
            return f'warning: Backup job for {serv} already exists'

    os.system(f"cp {full_path}/scripts/{script} {full_path}/{script}")

    commands = [
        f"chmod +x {full_path}/{script} && {full_path}/{script} HOST={rserver} SERVER={serv} TYPE={backup_type} SSH_PORT={ssh_settings['port']} "
        f"TIME={time} RPATH={rpath} DELJOB={deljob} USER={ssh_settings['user']} KEY={ssh_settings['key']}"
    ]

    output, error = server_mod.subprocess_execute(commands[0])

    try:
        os.remove(f'{full_path}/{script}')
    except Exception:
        pass

    for line in output:
        if any(s in line for s in ("Traceback", "FAILED")):
            try:
                return f'error: {line}'
            except Exception:
                return f'error: {output}'
    else:
        if not deljob and not update:
            if backup_sql.insert_backup_job(serv, rserver, rpath, backup_type, time, cred, description):
                roxywi_common.logging('backup ', f' a new backup job for server {serv} has been created', roxywi=1,
                                      login=1)
                return render_template(
                    'ajax/new_backup.html', backups=backup_sql.select_backups(server=serv, rserver=rserver), sshs=cred_sql.select_ssh()
                )

            else:
                raise Exception('error: Cannot add the job into DB')
        elif deljob:
            backup_sql.delete_backups(deljob)
            roxywi_common.logging('backup ', f' a backup job for server {serv} has been deleted', roxywi=1, login=1)
            return 'ok'
        elif update:
            backup_sql.update_backup(serv, rserver, rpath, backup_type, time, cred, description, update)
            roxywi_common.logging('backup ', f' a backup job for server {serv} has been updated', roxywi=1, login=1)
            return 'ok'


def s3_backup(server, s3_server, bucket, secret_key, access_key, time, deljob, description) -> str:
    if deljob:
        time = ''
        secret_key = ''
        access_key = ''
        tag = 'delete'
    else:
        tag = 'add'
        if backup_sql.check_exists_s3_backup(server):
            raise Exception(f'error: Backup job for {server} already exists')

    inv = {"server": {"hosts": {}}}
    inv["server"]["hosts"]["localhost"] = {
        "SERVER": server,
        "S3_SERVER": s3_server,
        "BUCKET": bucket,
        "SECRET_KEY": secret_key,
        "ACCESS_KEY": access_key,
        "TIME": time,
        "action": tag
    }

    try:
        installation_mod.run_ansible(inv, [], 's3_backup')
    except Exception as e:
        raise Exception(f'error: {e}')

    if not deljob:
        try:
            backup_sql.insert_s3_backup_job(server, s3_server, bucket, secret_key, access_key, time, description)
        except Exception as e:
            raise Exception(e)
        roxywi_common.logging('backup ', f' a new S3 backup job for server {server} has been created', roxywi=1, login=1)
        return render_template('ajax/new_s3_backup.html', backups=backup_sql.select_s3_backups(server=server, s3_server=s3_server, bucket=bucket))
    elif deljob:
        backup_sql.delete_s3_backups(deljob)
        roxywi_common.logging('backup ', f' a S3 backup job for server {server} has been deleted', roxywi=1, login=1)
        return 'ok'


def git_backup(server_id, service_id, git_init, repo, branch, period, cred, deljob, description, backup_id) -> str:
    servers = roxywi_common.get_dick_permit()
    proxy = sql.get_setting('proxy')
    services = service_sql.select_services()
    server_ip = server_sql.select_server_ip_by_id(server_id)
    service_name = service_sql.select_service_name_by_id(service_id).lower()
    service_config_dir = sql.get_setting(service_name + '_dir')
    script = 'git_backup.sh'
    proxy_serv = ''
    ssh_settings = ssh_mod.return_ssh_keys_path('localhost', id=int(cred))
    full_path = '/var/www/haproxy-wi/app'

    os.system(f"cp {full_path}/scripts/{script} {full_path}/{script}")

    if proxy is not None and proxy != '' and proxy != 'None':
        proxy_serv = proxy

    if repo is None or git_init == '0':
        repo = ''
    if branch is None or branch == '0':
        branch = 'main'

    commands = [
        f"chmod +x {full_path}/{script} && {full_path}/{script} HOST={server_ip} DELJOB={deljob} SERVICE={service_name} INIT={git_init} "
        f"SSH_PORT={ssh_settings['port']} PERIOD={period} REPO={repo} BRANCH={branch} CONFIG_DIR={service_config_dir} "
        f"PROXY={proxy_serv} USER={ssh_settings['user']} KEY={ssh_settings['key']}"
    ]

    output, error = server_mod.subprocess_execute(commands[0])

    try:
        os.remove(f'{full_path}/{script}')
    except Exception:
        pass

    for line in output:
        if any(s in line for s in ("Traceback", "FAILED")):
            try:
                return 'error: ' + line
            except Exception:
                return 'error: ' + output
    else:
        if deljob == '0':
            if backup_sql.insert_new_git(
                    server_id=server_id, service_id=service_id, repo=repo, branch=branch,
                    period=period, cred=cred, description=description
            ):
                gits = backup_sql.select_gits(server_id=server_id, service_id=service_id)
                sshs = cred_sql.select_ssh()

                lang = roxywi_common.get_user_lang_for_flask()
                roxywi_common.logging(
                    server_ip, ' A new git job has been created', roxywi=1, login=1, keep_history=1,
                    service=service_name
                )
                return render_template('ajax/new_git.html', gits=gits, sshs=sshs, servers=servers, services=services, new_add=1, lang=lang)
        else:
            if backup_sql.delete_git(backup_id):
                return 'ok'
