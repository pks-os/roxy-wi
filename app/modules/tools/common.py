import distro

import modules.db.sql as sql
import modules.roxywi.roxy as roxywi_mod
import modules.server.server as server_mod


def get_services_status(update_cur_ver=0):
    services = []
    if update_cur_ver:
        try:
            update_cur_tool_versions()
        except Exception as e:
            raise Exception(f'error: Update current versions: {e}')

    services_name = sql.get_all_tools()

    try:
        for s, v in services_name.items():
            status = is_tool_active(s)
            services.append([s, status, v])
    except Exception as e:
        raise Exception(f'error: Cannot get tools status: {e}')

    return services


def update_roxy_wi(service: str) -> str:
    restart_service = ''
    services = sql.get_roxy_tools()

    if service not in services:
        raise Exception(f'error: {service} is not part of Roxy-WI')

    if distro.id() == 'ubuntu':
        try:
            if service == 'roxy-wi-keep_alive':
                service = 'roxy-wi-keep-alive'
        except Exception:
            pass

        if service != 'roxy-wi':
            restart_service = f'&& sudo systemctl restart {service}'

        cmd = f'sudo -S apt-get update && sudo apt-get install {service} {restart_service} -y'
    else:
        if service != 'roxy-wi':
            restart_service = f'&& sudo systemctl restart {service}'
        cmd = f'sudo -S yum -y install {service} {restart_service}'

    output, stderr = server_mod.subprocess_execute(cmd)
    update_cur_tool_version(service)

    if stderr != '':
        return str(stderr)
    else:
        return str(output)


def is_tool_active(tool_name: str) -> str:
    is_in_docker = roxywi_mod.is_docker()
    if is_in_docker:
        cmd = f"sudo supervisorctl status {tool_name}|awk '{{print $2}}'"
    else:
        cmd = f"systemctl is-active {tool_name}"
    status, stderr = server_mod.subprocess_execute(cmd)
    return status[0]


def update_cur_tool_versions() -> None:
    tools = sql.get_all_tools()
    for s, v in tools.items():
        update_cur_tool_version(s)


def update_cur_tool_version(tool_name: str) -> None:
    correct_name = tool_name
    if tool_name == 'grafana-server':
        correct_name = 'grafana'
    if tool_name == 'prometheus':
        cmd = "prometheus --version 2>&1 |grep prometheus|awk '{print $3}'"
    else:
        if distro.id() == 'ubuntu':
            if tool_name == 'roxy-wi-keep_alive':
                correct_name = 'roxy-wi-keep-alive'
            cmd = f"apt list --installed 2>&1 |grep {correct_name}|awk '{{print $2}}'|sed 's/-/./'"
        else:
            cmd = f"rpm -q {correct_name}|awk -F\"{correct_name}\" '{{print $2}}' |awk -F\".noa\" '{{print $1}}' |sed 's/-//1' |sed 's/-/./'"

    service_ver, stderr = server_mod.subprocess_execute(cmd)

    try:
        service_ver = service_ver[0]
    except Exception:
        service_ver = 0

    if service_ver in ('command', 'prometheus:', 'not'):
        service_ver = 0

    try:
        sql.update_tool_cur_version(tool_name, service_ver)
    except Exception:
        pass


def get_cur_tool_version(tool_name: str) -> str:
    return sql.get_tool_cur_version(tool_name)