import os
import re

import distro
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

import app.modules.db.sql as sql
import app.modules.db.roxy as roxy_sql
import app.modules.common.common as common
import app.modules.roxywi.common as roxywi_common
import app.modules.server.server as server_mod


def is_docker() -> bool:
	path = "/proc/self/cgroup"
	if not os.path.isfile(path):
		return False
	with open(path) as f:
		for line in f:
			if re.match("\d+:[\w=]+:/docker(-[ce]e)?/\w+", line):
				return True
	return_out = server_mod.subprocess_execute_with_rc('systemctl status rsyslog')
	if return_out['rc']:
		return True
	return False

def check_ver():
	return roxy_sql.get_ver()


def versions():
	try:
		current_ver = check_ver()
		current_ver_without_dots = current_ver.split('.')
		current_ver_without_dots = ''.join(current_ver_without_dots)
		current_ver_without_dots = current_ver_without_dots.replace('\n', '')
		current_ver_without_dots = int(current_ver_without_dots)
	except Exception:
		current_ver = "Cannot get current version"
		current_ver_without_dots = 0

	try:
		new_ver = check_new_version('roxy-wi')
		new_ver_without_dots = new_ver.split('.')
		new_ver_without_dots = ''.join(new_ver_without_dots)
		new_ver_without_dots = new_ver_without_dots.replace('\n', '')
		new_ver_without_dots = int(new_ver_without_dots)
	except Exception as e:
		new_ver = "Cannot get a new version"
		new_ver_without_dots = 0
		roxywi_common.logging('Roxy-WI server', f' {e}', roxywi=1)

	return current_ver, new_ver, current_ver_without_dots, new_ver_without_dots


def check_new_version(service):
	current_ver = check_ver()
	res = ''
	proxy_dict = common.return_proxy_dict()

	try:
		response = requests.get(f'https://roxy-wi.org/version/get/{service}', timeout=5, proxies=proxy_dict)
		if service == 'roxy-wi':
			requests.get(f'https://roxy-wi.org/version/send/{current_ver}', timeout=5, proxies=proxy_dict)

		res = response.content.decode(encoding='UTF-8')
	except requests.exceptions.RequestException as e:
		roxywi_common.logging('Roxy-WI server', f' {e}', roxywi=1)

	return res


def update_user_status() -> None:
	user_license = sql.get_setting('license')
	proxy_dict = common.return_proxy_dict()
	retry_strategy = Retry(
		total=3,
		status_forcelist=[429, 500, 502, 503, 504]
	)
	adapter = HTTPAdapter(max_retries=retry_strategy)
	roxy_wi_get_plan = requests.Session()
	roxy_wi_get_plan.mount("https://", adapter)
	json_body = {'license': user_license}
	roxy_wi_get_plan = requests.post('https://roxy-wi.org/user/license', timeout=5, proxies=proxy_dict, json=json_body)
	try:
		status = roxy_wi_get_plan.json()
		roxy_sql.update_user_status(status['status'], status['plan'], status['method'])
	except Exception as e:
		roxywi_common.logging('Roxy-WI server', f'error: Cannot get user status {e}', roxywi=1)


def action_service(action: str, service: str) -> str:
	is_in_docker = is_docker()
	actions = {
		'start': 'enable --now',
		'stop': 'disable --now',
		'restart': 'restart',
	}
	cmd = f"sudo systemctl {actions[action]} {service}"
	if not roxy_sql.select_user_status():
		return 'warning: The service is disabled because you are not subscribed. Read <a href="https://roxy-wi.org/pricing" ' \
				   'title="Roxy-WI pricing" target="_blank">here</a> about subscriptions'
	if is_in_docker:
		cmd = f"sudo supervisorctl {action} {service}"
	os.system(cmd)
	roxywi_common.logging('Roxy-WI server', f' The service {service} has been {action}ed', roxywi=1, login=1)
	return 'ok'


def update_plan():
	try:
		if distro.id() == 'ubuntu':
			path_to_repo = '/etc/apt/auth.conf.d/roxy-wi.conf'
			cmd = "grep login /etc/apt/auth.conf.d/roxy-wi.conf |awk '{print $2}'"
			cmd2 = "grep password /etc/apt/auth.conf.d/roxy-wi.conf |awk '{print $2}'"
		else:
			path_to_repo = '/etc/yum.repos.d/roxy-wi.repo'
			cmd = "grep base /etc/yum.repos.d/roxy-wi.repo |grep -v '#' |awk -F\":\" '{print $2}'|awk -F\"/\" '{print $3}'"
			cmd2 = "grep base /etc/yum.repos.d/roxy-wi.repo |grep -v '#' |awk -F\":\" '{print $3}'|awk -F\"@\" '{print $1}'"
		if os.path.exists(path_to_repo):
			get_user_name, stderr = server_mod.subprocess_execute(cmd)
			user_name = get_user_name[0]
			cur_license = sql.get_setting('license')
			if not cur_license:
				get_license, stderr = server_mod.subprocess_execute(cmd2)
				user_license = get_license[0]

				if user_license:
					try:
						sql.update_setting('license', user_license, 1)
					except Exception as e:
						roxywi_common.logging('Roxy-WI server', f'error: Cannot update license {e}', roxywi=1)
		else:
			user_name = 'git'

		if roxy_sql.select_user_name():
			roxy_sql.update_user_name(user_name)
		else:
			roxy_sql.insert_user_name(user_name)
	except Exception as e:
		roxywi_common.logging('Cannot update subscription: ', str(e), roxywi=1)

	update_user_status()
