import os

from flask import render_template, request

import app.modules.db.sql as sql
import app.modules.db.add as add_sql
import app.modules.db.server as server_sql
import app.modules.server.ssh as ssh_mod
import app.modules.common.common as common
import app.modules.config.config as config_mod
import app.modules.config.common as config_common
import app.modules.server.server as server_mod
import app.modules.roxywi.common as roxywi_common
import app.modules.service.common as service_common
import app.modules.roxy_wi_tools as roxy_wi_tools

get_config = roxy_wi_tools.GetConfigVar()


def save_to_haproxy_config(config: str, server_ip: str, name: str) -> str:
	roxywi_common.check_is_server_in_group(server_ip)
	cfg = config_common.generate_config_path('haproxy', server_ip)

	config_mod.get_config(server_ip, cfg)

	try:
		with open(cfg, "a") as conf:
			conf.write(config)
	except IOError as e:
		raise Exception(f"error: Cannot read import config file {e}")

	try:
		output = config_mod.master_slave_upload_and_restart(server_ip, cfg, "save", 'haproxy')
	except Exception as e:
		raise Exception(e)

	try:
		roxywi_common.logging(server_ip, f"Add has been added a new {name}")
	except Exception:
		pass

	if output:
		return output
	else:
		return name


def save_nginx_config(config_add: str, server_ip: str, config_name: str) -> str:
	roxywi_common.check_is_server_in_group(server_ip)
	sub_folder = 'conf.d' if 'upstream' in config_name else 'sites-enabled'

	cfg = config_common.generate_config_path('nginx', server_ip)
	nginx_dir = common.return_nice_path(sql.get_setting('nginx_dir'))

	config_file_name = f'{nginx_dir}{sub_folder}/{config_name}.conf'

	try:
		with open(cfg, "w") as conf:
			conf.write(config_add)
	except IOError:
		return "error: Cannot save a new config"

	try:
		roxywi_common.logging(server_ip, "add/nginx add new %s" % config_name)
	except Exception:
		pass

	output = config_mod.master_slave_upload_and_restart(server_ip, cfg, "save", 'nginx', config_file_name=config_file_name)

	if output:
		return output
	else:
		return config_name


def get_userlists(config):
	return_config = ''
	with open(config, 'r') as f:
		for line in f:
			if line.startswith('userlist'):
				line = line.strip()
				return_config += line + ','

	return return_config


def show_userlist(server_ip: str) -> str:
	configs_dir = get_config.get_config_var('configs', 'haproxy_save_configs_dir')
	format_file = 'cfg'

	try:
		sections = get_userlists(configs_dir + roxywi_common.get_files(configs_dir, format_file)[0])
	except Exception as e:
		roxywi_common.logging('Roxy-WI server', str(e), roxywi=1)
		try:
			cfg = config_common.generate_config_path('haproxy', server_ip)
		except Exception as e:
			roxywi_common.logging('Roxy-WI server', f' Cannot generate a cfg path {e}', roxywi=1)
		try:
			config_mod.get_config(server_ip, cfg)
		except Exception as e:
			roxywi_common.logging('Roxy-WI server', f' Cannot download a config {e}', roxywi=1)
		try:
			sections = get_userlists(cfg)
		except Exception as e:
			roxywi_common.logging('Roxy-WI server', f' Cannot get Userlists from the config file {e}', roxywi=1)
			sections = 'error: Cannot get Userlists'

	return sections


def add_userlist() -> str:
	generate = request.form.get('generateconfig')
	server_ip = request.form.get('serv')
	name = f"userlist {request.form.get('new_userlist')}\n"

	new_userlist_groups = ""
	if request.form.get('userlist-group') is not None:
		groups = request.form.getlist('userlist-group')
		for group in groups:
			if group == '':
				continue
			new_userlist_groups += f"    group {group}\n"

	new_users_list = ""
	if request.form.get('userlist-user') is not None:
		users = request.form.getlist('userlist-user')
		passwords = request.form.getlist('userlist-password')
		userlist_user_group = request.form.getlist('userlist-user-group')
		i = 0

		for user in users:
			if user == '':
				continue
			try:
				group = f' groups {userlist_user_group[i]}'
			except Exception:
				group = ''
			new_users_list += f"    user {user} insecure-password {passwords[i]} {group}\n"
			i += 1

	config_add = "\n" + name + new_userlist_groups + new_users_list

	if generate:
		return config_add
	else:
		try:
			return save_to_haproxy_config(config_add, server_ip, name)
		except Exception as e:
			return str(e)


def get_bwlist(color: str, group: str, list_name: str) -> str:
	lib_path = get_config.get_config_var('main', 'lib_path')
	list_path = f"{lib_path}/lists/{group}/{color}/{list_name}"

	try:
		with open(list_path, 'r') as f:
			return f.read()
	except IOError as e:
		return f"error: Cannot read {color} list: {e}"


def get_bwlists_for_autocomplete(color: str, group: str) -> str:
	lib_path = get_config.get_config_var('main', 'lib_path')
	list_path = f"{lib_path}/lists/{group}/{color}"
	lists = roxywi_common.get_files(list_path, "lst")
	lines = ''

	for line in lists:
		lines += line + ' '

	return lines


def create_bwlist(server_ip: str, list_name: str, color: str, group: str) -> str:
	lib_path = get_config.get_config_var('main', 'lib_path')
	list_name = f"{list_name.split('.')[0]}.lst"
	list_path = f"{lib_path}/lists/{group}/{color}/{list_name}"
	try:
		open(list_path, 'a').close()
		try:
			roxywi_common.logging(server_ip, f'A new list {color} {list_name} has been created', roxywi=1, login=1)
		except Exception:
			pass
		return 'success: '
	except IOError as e:
		return f'error: Cannot create a new {color} list. {e}, '


def save_bwlist(list_name: str, list_con: str, color: str, group: str, server_ip: str, action: str) -> str:
	lib_path = get_config.get_config_var('main', 'lib_path')
	list_path = f"{lib_path}/lists/{group}/{color}/{list_name}"
	path = sql.get_setting('haproxy_dir') + "/" + color
	servers = []
	output = ''

	try:
		with open(list_path, "w") as file:
			file.write(list_con)
	except IOError as e:
		return f'error: Cannot save {color} list. {e}'

	if server_ip != 'all':
		servers.append(server_ip)

		masters = server_sql.is_master(server_ip)
		for master in masters:
			if master[0] is not None:
				servers.append(master[0])
	else:
		server = roxywi_common.get_dick_permit()
		for s in server:
			servers.append(s[2])

	for serv in servers:
		server_mod.ssh_command(serv, f"sudo mkdir {path}")
		server_mod.ssh_command(serv, f"sudo chown $(whoami) {path}")
		try:
			config_mod.upload(serv, f'{path}/{list_name}', list_path)
		except Exception as e:
			output += f'error: Upload fail: to {serv}: {e} , '

		output += f'success: Edited {color} list was uploaded to {serv} , '
		try:
			roxywi_common.logging(serv, f'Has been edited the {color} list {list_name}', roxywi=1, login=1)
		except Exception:
			pass

		server_id = server_sql.select_server_id_by_ip(server_ip=serv)
		haproxy_service_name = service_common.get_correct_service_name('haproxy', server_id)

		if action == 'restart':
			server_mod.ssh_command(serv, f"sudo systemctl restart {haproxy_service_name}")
		elif action == 'reload':
			server_mod.ssh_command(serv, f"sudo systemctl reload {haproxy_service_name}")

	return output


def delete_bwlist(list_name: str, color: str, group: str, server_ip: str) -> str:
	servers = []
	lib_path = get_config.get_config_var('main', 'lib_path')
	list_path = f"{lib_path}/lists/{group}/{color}/{list_name}"
	path = f"{sql.get_setting('haproxy_dir')}/{color}"
	output = ''

	try:
		os.remove(list_path)
	except IOError as e:
		return f'error: Cannot delete {color} list from Roxy-WI server. {e} , '

	if server_ip != 'all':
		servers.append(server_ip)

		masters = server_sql.is_master(server_ip)
		for master in masters:
			if master[0] is not None:
				servers.append(master[0])
	else:
		server = roxywi_common.get_dick_permit()
		for s in server:
			servers.append(s[2])

	for serv in servers:
		try:
			server_mod.ssh_command(serv, f"sudo rm {path}/{list_name}")
		except Exception as e:
			return f'error: Deleting fail: {e} , '

		output += f'success: the {color} list has been deleted on {serv} , '
		roxywi_common.logging(serv, f'has been deleted the {color} list {list_name}', roxywi=1, login=1)
	return output


def edit_map(map_name: str, group: str) -> str:
	lib_path = get_config.get_config_var('main', 'lib_path')
	list_path = f"{lib_path}/maps/{group}/{map_name}"

	try:
		with open(list_path, 'r') as f:
			read_map = f.read()
	except IOError as e:
		return f"error: Cannot read {map_name} list: {e}"
	else:
		return read_map


def create_map(server_ip: str, map_name: str, group: str) -> str:
	lib_path = get_config.get_config_var('main', 'lib_path')
	map_name = f"{map_name.split('.')[0]}.map"
	map_path = f'{lib_path}/maps/{group}/'
	full_path = f'{map_path}{map_name}'

	try:
		server_mod.subprocess_execute(f'sudo mkdir -p {map_path}')
		common.set_correct_owner(lib_path)
	except Exception as e:
		raise Exception(f'error: cannot create a local folder for maps: {e}')
	try:
		os.mknod(full_path)
		roxywi_common.logging(server_ip, f'A new map {map_name} has been created', roxywi=1, login=1)
	except IOError as e:
		raise Exception(f'error: Cannot create a new {map_name} map. {e}')
	else:
		return 'success: '


def save_map(map_name: str, list_con: str, group: str, server_ip: str, action: str) -> str:
	lib_path = get_config.get_config_var('main', 'lib_path')
	map_path = f"{lib_path}/maps/{group}/{map_name}"
	output = ''

	try:
		with open(map_path, "w") as file:
			file.write(list_con)
	except IOError as e:
		return f'error: Cannot save {map_name} list. {e}'

	path = sql.get_setting('haproxy_dir') + "/maps"
	servers = []

	if server_ip != 'all':
		servers.append(server_ip)

		masters = server_sql.is_master(server_ip)
		for master in masters:
			if master[0] is not None:
				servers.append(master[0])
	else:
		server = roxywi_common.get_dick_permit()
		for s in server:
			servers.append(s[2])

	for serv in servers:
		server_mod.ssh_command(serv, f"sudo mkdir {path}")
		server_mod.ssh_command(serv, f"sudo chown $(whoami) {path}")
		try:
			config_mod.upload(serv, f'{path}/{map_name}', map_path)
		except Exception as e:
			output += f'error: Upload fail to: {serv}: {e} , '

		try:
			roxywi_common.logging(serv, f'Has been edited the map {map_name}', roxywi=1, login=1)
		except Exception:
			pass

		server_id = server_sql.select_server_id_by_ip(server_ip=serv)
		haproxy_service_name = service_common.get_correct_service_name('haproxy', server_id)

		if action == 'restart':
			server_mod.ssh_command(serv, f"sudo systemctl restart {haproxy_service_name}")
		elif action == 'reload':
			server_mod.ssh_command(serv, f"sudo systemctl reload {haproxy_service_name}")

		output += f'success: Edited {map_name} map was uploaded to {serv} , '

	return output


def delete_map(map_name: str, group: str, server_ip: str) -> str:
	servers = []
	lib_path = get_config.get_config_var('main', 'lib_path')
	list_path = f"{lib_path}/maps/{group}/{map_name}"
	path = f"{sql.get_setting('haproxy_dir')}/maps"
	output = ''

	try:
		os.remove(list_path)
	except IOError as e:
		return f'error: Cannot delete {map_name} map from Roxy-WI server. {e} , '

	if server_ip != 'all':
		servers.append(server_ip)

		masters = server_sql.is_master(server_ip)
		for master in masters:
			if master[0] is not None:
				servers.append(master[0])
	else:
		server = roxywi_common.get_dick_permit()
		for s in server:
			servers.append(s[2])

	for serv in servers:
		try:
			server_mod.ssh_command(serv, f"sudo rm {path}/{map_name}")
		except Exception as e:
			return f'error: Deleting fail: {e} , '

		roxywi_common.logging(serv, f'has been deleted the {map_name} map', roxywi=1, login=1)
		output += f'success: the {map_name} map has been deleted on {serv} , '

	return output


def create_saved_option(option: str, group: int) -> str:
	if add_sql.insert_new_option(option, group):
		return render_template('ajax/new_option.html', options=add_sql.select_options(option=option))


def get_saved_option(group: str, term: str) -> dict:
	options = add_sql.select_options(group=group, term=term)
	a = {}
	v = 0

	for i in options:
		a[v] = i.options
		v = v + 1

	return a


def update_saved_option(option, option_id) -> bool:
	try:
		add_sql.update_options(option, option_id)
	except Exception as e:
		raise Exception(e)
	else:
		return True


def create_saved_server(server: str, group: str, desc: str) -> str:
	if add_sql.insert_new_saved_server(server, desc, group):
		return render_template('ajax/new_saved_servers.html', server=add_sql.select_saved_servers(server=server))


def get_saved_servers(group: str, term: str) -> dict:
	servers = add_sql.select_saved_servers(group=group, term=term)
	a = {}
	v = 0
	for i in servers:
		a[v] = {}
		a[v]['value'] = {}
		a[v]['desc'] = {}
		a[v]['value'] = i.server
		a[v]['desc'] = i.description
		v = v + 1

	return a


def get_le_cert(server_ip: str, lets_domain: str, lets_email: str) -> str:
	proxy = sql.get_setting('proxy')
	ssl_path = common.return_nice_path(sql.get_setting('cert_path'), is_service=0)
	haproxy_dir = sql.get_setting('haproxy_dir')
	script = "letsencrypt.sh"
	proxy_serv = ''
	ssh_settings = ssh_mod.return_ssh_keys_path(server_ip)
	full_path = '/var/www/haproxy-wi/app'

	os.system(f"cp {full_path}/scripts/{script} {full_path}/{script}")

	if proxy is not None and proxy != '' and proxy != 'None':
		proxy_serv = proxy

	commands = [
		f"chmod +x {full_path}/{script} && {full_path}/{script} PROXY={proxy_serv} haproxy_dir={haproxy_dir} DOMAIN={lets_domain} "
		f"EMAIL={lets_email} SSH_PORT={ssh_settings['port']} SSL_PATH={ssl_path} HOST={server_ip} USER={ssh_settings['user']} "
		f"PASS='{ssh_settings['password']}' KEY={ssh_settings['key']}"
	]

	output, error = server_mod.subprocess_execute(commands[0])

	if error:
		roxywi_common.logging('Roxy-WI server', error, roxywi=1)
		return error
	else:
		for line in output:
			if any(s in line for s in ("msg", "FAILED")):
				try:
					line = line.split(':')[1]
					line = line.split('"')[1]
					return line + "<br>"
				except Exception:
					return output
		else:
			os.remove(f'{full_path}/{script}')
			return 'success: Certificate has been created'


def get_ssl_cert(server_ip: str, cert_id: int) -> str:
	cert_path = sql.get_setting('cert_path')
	command = f"openssl x509 -in {cert_path}/{cert_id} -text"

	try:
		return server_mod.ssh_command(server_ip, command)
	except Exception as e:
		return f'error: Cannot connect to the server {e}'


def get_ssl_raw_cert(server_ip: str, cert_id: str) -> str:
	cert_path = sql.get_setting('cert_path')
	command = f"cat {cert_path}/{cert_id}"

	try:
		return server_mod.ssh_command(server_ip, command)
	except Exception as e:
		return f'error: Cannot connect to the server {e}'


def get_ssl_certs(server_ip: str) -> str:
	cert_path = sql.get_setting('cert_path')
	command = f"sudo ls -1t {cert_path} |grep -E 'pem|crt|key'"
	try:
		return server_mod.ssh_command(server_ip, command)
	except Exception as e:
		return f'error: Cannot connect to the server: {e}'


def del_ssl_cert(server_ip: str, cert_id: str) -> str:
	cert_path = sql.get_setting('cert_path')
	command = f"sudo rm -f {cert_path}/{cert_id}"

	try:
		return server_mod.ssh_command(server_ip, command)
	except Exception as e:
		return f'error: Cannot delete the certificate {e}'


def upload_ssl_cert(server_ip: str, ssl_name: str, ssl_cont: str) -> list[str]:
	cert_path = sql.get_setting('cert_path')
	tmp_path = sql.get_setting('tmp_config_path')
	output = []
	server_ip = str(server_ip)

	if ssl_name is None:
		raise Exception('Please enter a desired name')
	else:
		name = f"{ssl_name}.pem"
		path_to_file = f"{tmp_path}/{ssl_name}.pem"

	try:
		with open(path_to_file, "w") as ssl_cert:
			ssl_cert.write(ssl_cont)
	except IOError as e:
		raise IOError(f'Cannot save the SSL key file: {e}')

	masters = server_sql.is_master(server_ip)
	for master in masters:
		if master[0] is not None:
			config_mod.upload(master[0], f'{cert_path}/{name}', path_to_file)
			output.append(f'success: the SSL file has been uploaded to {master[0]} into: {cert_path}/{name}')
	try:
		config_mod.upload(server_ip, f'{cert_path}/{name}', path_to_file)
		output.append(f'success: the SSL file has been uploaded to {server_ip} into: {cert_path}/{name}')
	except Exception as e:
		roxywi_common.logging('Roxy-WI server', str(e), roxywi=1)
		raise Exception(f'Cannot upload SSL cert: {e}')

	roxywi_common.logging(server_ip, f"A new certificate {name} has been uploaded to {server_ip}", roxywi=1, login=1)
	return output
