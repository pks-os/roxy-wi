#!/usr/bin/env python3
import distro

from modules.db.db_model import *


conn = connect()
migrator = connect(get_migrator=1)


def default_values():
	if distro.id() == 'ubuntu':
		apache_dir = 'apache2'
	else:
		apache_dir = 'httpd'
	data_source = [
		{'param': 'time_zone', 'value': 'UTC', 'section': 'main', 'desc': 'Time Zone', 'group': '1'},
		{'param': 'license', 'value': '', 'section': 'main', 'desc': 'License key', 'group': '1'},
		{'param': 'proxy', 'value': '', 'section': 'main', 'desc': 'IP address and port of the proxy server. Use proto://ip:port', 'group': '1'},
		{'param': 'session_ttl', 'value': '5', 'section': 'main', 'desc': 'TTL for a user session (in days)', 'group': '1'},
		{'param': 'token_ttl', 'value': '5', 'section': 'main', 'desc': 'TTL for a user token (in days)', 'group': '1'},
		{'param': 'tmp_config_path', 'value': '/tmp/', 'section': 'main',
			'desc': 'Path to the temporary directory. A valid path should be specified as the value of this parameter. '
					'The directory must be owned by the user specified in SSH settings', 'group': '1'},
		{'param': 'cert_path', 'value': '/etc/ssl/certs/', 'section': 'main',
			'desc': 'Path to SSL dir. Folder owner must be a user which set in the SSH settings. Path must exist', 'group': '1'},
		{'param': 'maxmind_key', 'value': '', 'section': 'main', 'desc': 'License key for downloading GeoIP DB. You can create it on maxmind.com', 'group': '1'},
		{'param': 'haproxy_path_logs', 'value': '/var/log/haproxy/', 'section': 'haproxy', 'desc': 'The path for HAProxy logs', 'group': '1'},
		{'param': 'syslog_server_enable', 'value': '0', 'section': 'logs', 'desc': 'Enable getting logs from a syslog server', 'group': '1'},
		{'param': 'syslog_server', 'value': '', 'section': 'logs', 'desc': 'IP address of the syslog_server', 'group': '1'},
		{'param': 'log_time_storage', 'value': '14', 'section': 'logs', 'desc': 'Retention period for user activity logs (in days)', 'group': '1'},
		{'param': 'haproxy_stats_user', 'value': 'admin', 'section': 'haproxy', 'desc': 'Username for accessing HAProxy stats page', 'group': '1'},
		{'param': 'haproxy_stats_password', 'value': 'password', 'section': 'haproxy', 'desc': 'Password for accessing HAProxy stats page', 'group': '1'},
		{'param': 'haproxy_stats_port', 'value': '8085', 'section': 'haproxy', 'desc': 'Port for HAProxy stats page', 'group': '1'},
		{'param': 'haproxy_stats_page', 'value': 'stats', 'section': 'haproxy', 'desc': 'URI for HAProxy stats page', 'group': '1'},
		{'param': 'haproxy_dir', 'value': '/etc/haproxy', 'section': 'haproxy', 'desc': 'Path to the HAProxy directory', 'group': '1'},
		{'param': 'haproxy_config_path', 'value': '/etc/haproxy/haproxy.cfg', 'section': 'haproxy', 'desc': 'Path to the HAProxy configuration file', 'group': '1'},
		{'param': 'server_state_file', 'value': '/etc/haproxy/haproxy.state', 'section': 'haproxy', 'desc': 'Path to the HAProxy state file', 'group': '1'},
		{'param': 'haproxy_sock', 'value': '/var/run/haproxy.sock', 'section': 'haproxy', 'desc': 'Socket port for HAProxy', 'group': '1'},
		{'param': 'haproxy_sock_port', 'value': '1999', 'section': 'haproxy', 'desc': 'HAProxy sock port', 'group': '1'},
		{'param': 'haproxy_container_name', 'value': 'haproxy', 'section': 'haproxy', 'desc': 'Docker container name for HAProxy service', 'group': '1'},
		{'param': 'apache_log_path', 'value': f'/var/log/{apache_dir}/', 'section': 'logs', 'desc': 'Path to Apache logs. Apache service for Roxy-WI', 'group': '1'},
		{'param': 'nginx_path_logs', 'value': '/var/log/nginx/', 'section': 'nginx', 'desc': 'The path for NGINX logs', 'group': '1'},
		{'param': 'nginx_stats_user', 'value': 'admin', 'section': 'nginx', 'desc': 'Username for accessing NGINX stats page', 'group': '1'},
		{'param': 'nginx_stats_password', 'value': 'password', 'section': 'nginx', 'desc': 'Password for Stats web page NGINX', 'group': '1'},
		{'param': 'nginx_stats_port', 'value': '8086', 'section': 'nginx', 'desc': 'Stats port for web page NGINX', 'group': '1'},
		{'param': 'nginx_stats_page', 'value': 'stats', 'section': 'nginx', 'desc': 'URI Stats for web page NGINX', 'group': '1'},
		{'param': 'nginx_dir', 'value': '/etc/nginx/', 'section': 'nginx', 'desc': 'Path to the NGINX directory with config files', 'group': '1'},
		{'param': 'nginx_config_path', 'value': '/etc/nginx/nginx.conf', 'section': 'nginx', 'desc': 'Path to the main NGINX configuration file', 'group': '1'},
		{'param': 'nginx_container_name', 'value': 'nginx', 'section': 'nginx', 'desc': 'Docker container name for NGINX service', 'group': '1'},
		{'param': 'ldap_enable', 'value': '0', 'section': 'ldap', 'desc': 'Enable LDAP', 'group': '1'},
		{'param': 'ldap_server', 'value': '', 'section': 'ldap', 'desc': 'IP address of the LDAP server', 'group': '1'},
		{'param': 'ldap_port', 'value': '389', 'section': 'ldap', 'desc': 'LDAP port (port 389 or 636 is used by default)', 'group': '1'},
		{'param': 'ldap_user', 'value': '', 'section': 'ldap', 'desc': 'LDAP username. Format: user@domain.com', 'group': '1'},
		{'param': 'ldap_password', 'value': '', 'section': 'ldap', 'desc': 'LDAP password', 'group': '1'},
		{'param': 'ldap_base', 'value': '', 'section': 'ldap', 'desc': 'Base domain. Example: dc=domain, dc=com', 'group': '1'},
		{'param': 'ldap_domain', 'value': '', 'section': 'ldap', 'desc': 'LDAP domain for logging in', 'group': '1'},
		{'param': 'ldap_class_search', 'value': 'user', 'section': 'ldap', 'desc': 'Class for searching the user', 'group': '1'},
		{'param': 'ldap_user_attribute', 'value': 'userPrincipalName', 'section': 'ldap', 'desc': 'Attribute to search users by', 'group': '1'},
		{'param': 'ldap_search_field', 'value': 'mail', 'section': 'ldap', 'desc': 'User\'s email address', 'group': '1'},
		{'param': 'ldap_type', 'value': '0', 'section': 'ldap', 'desc': 'Use LDAPS', 'group': '1'},
		{'param': 'port_scan_interval', 'value': '5', 'section': 'monitoring', 'desc': 'Check interval for Port scanner (in minutes)', 'group': '1'},
		{'param': 'portscanner_keep_history_range', 'value': '14', 'section': 'monitoring', 'desc': 'Retention period for Port scanner history', 'group': '1'},
		{'param': 'smon_keep_history_range', 'value': '14', 'section': 'smon', 'desc': 'Retention period for SMON history', 'group': '1'},
		{'param': 'checker_keep_history_range', 'value': '14', 'section': 'monitoring', 'desc': 'Retention period for Checker history', 'group': '1'},
		{'param': 'action_keep_history_range', 'value': '30', 'section': 'monitoring', 'desc': 'Retention period for Action history', 'group': '1'},
		{'param': 'checker_maxconn_threshold', 'value': '90', 'section': 'monitoring', 'desc': 'Threshold value for alerting, in %', 'group': '1'},
		{'param': 'checker_check_interval', 'value': '1', 'section': 'monitoring', 'desc': 'Check interval for Checker (in minutes)', 'group': '1'},
		{'param': 'smon_ssl_expire_warning_alert', 'value': '14', 'section': 'smon', 'desc': 'Warning alert about a SSL certificate expiration (in days)', 'group': '1'},
		{'param': 'smon_ssl_expire_critical_alert', 'value': '7', 'section': 'smon', 'desc': 'Critical alert about a SSL certificate expiration (in days)', 'group': '1'},
		{'param': 'master_ip', 'value': '', 'section': 'smon', 'desc': '', 'group': '1'},
		{'param': 'master_port', 'value': '5100', 'section': 'smon', 'desc': '', 'group': '1'},
		{'param': 'agent_port', 'value': '5101', 'section': 'smon', 'desc': '', 'group': '1'},
		{'param': 'rabbitmq_host', 'value': '127.0.0.1', 'section': 'rabbitmq', 'desc': 'RabbitMQ-server host', 'group': '1'},
		{'param': 'rabbitmq_port', 'value': '5672', 'section': 'rabbitmq', 'desc': 'RabbitMQ-server port', 'group': '1'},
		{'param': 'rabbitmq_port', 'value': '5672', 'section': 'rabbitmq', 'desc': 'RabbitMQ-server port', 'group': '1'},
		{'param': 'rabbitmq_vhost', 'value': '/', 'section': 'rabbitmq', 'desc': 'RabbitMQ-server vhost', 'group': '1'},
		{'param': 'rabbitmq_queue', 'value': 'roxy-wi', 'section': 'rabbitmq', 'desc': 'RabbitMQ-server queue', 'group': '1'},
		{'param': 'rabbitmq_user', 'value': 'roxy-wi', 'section': 'rabbitmq', 'desc': 'RabbitMQ-server user', 'group': '1'},
		{'param': 'rabbitmq_password', 'value': 'roxy-wi123', 'section': 'rabbitmq', 'desc': 'RabbitMQ-server user password', 'group': '1'},
		{'param': 'apache_path_logs', 'value': '/var/log/httpd/', 'section': 'apache', 'desc': 'The path for Apache logs', 'group': '1'},
		{'param': 'apache_stats_user', 'value': 'admin', 'section': 'apache', 'desc': 'Username for accessing Apache stats page', 'group': '1'},
		{'param': 'apache_stats_password', 'value': 'password', 'section': 'apache', 'desc': 'Password for Apache stats webpage', 'group': '1'},
		{'param': 'apache_stats_port', 'value': '8087', 'section': 'apache', 'desc': 'Stats port for webpage Apache', 'group': '1'},
		{'param': 'apache_stats_page', 'value': 'stats', 'section': 'apache', 'desc': 'URI Stats for webpage Apache', 'group': '1'},
		{'param': 'apache_dir', 'value': '/etc/httpd/', 'section': 'apache', 'desc': 'Path to the Apache directory with config files', 'group': '1'},
		{'param': 'apache_config_path', 'value': '/etc/httpd/conf/httpd.conf', 'section': 'apache', 'desc': 'Path to the main Apache configuration file', 'group': '1'},
		{'param': 'apache_container_name', 'value': 'apache', 'section': 'apache', 'desc': 'Docker container name for Apache service', 'group': '1'},
		{'param': 'keepalived_config_path', 'value': '/etc/keepalived/keepalived.conf', 'section': 'keepalived', 'desc': 'Path to the main Keepalived configuration file', 'group': '1'},
		{'param': 'keepalived_path_logs', 'value': '/var/log/keepalived/', 'section': 'keepalived', 'desc': 'The path for Keepalived logs', 'group': '1'},
		{'param': 'mail_ssl', 'value': '0', 'section': 'mail', 'desc': 'Enable TLS', 'group': '1'},
		{'param': 'mail_from', 'value': '', 'section': 'mail', 'desc': 'Address of sender', 'group': '1'},
		{'param': 'mail_smtp_host', 'value': '', 'section': 'mail', 'desc': 'SMTP server address', 'group': '1'},
		{'param': 'mail_smtp_port', 'value': '25', 'section': 'mail', 'desc': 'SMTP server port', 'group': '1'},
		{'param': 'mail_smtp_user', 'value': '', 'section': 'mail', 'desc': 'User for auth', 'group': '1'},
		{'param': 'mail_smtp_password', 'value': '', 'section': 'mail', 'desc': 'Password for auth', 'group': '1'},
	]
	try:
		Setting.insert_many(data_source).on_conflict_ignore().execute()
	except Exception as e:
		print(str(e))

	data_source = [
		{'username': 'admin', 'email': 'admin@localhost', 'password': '21232f297a57a5a743894a0e4a801fc3', 'role': '1', 'groups': '1'},
		{'username': 'editor', 'email': 'editor@localhost', 'password': '5aee9dbd2a188839105073571bee1b1f', 'role': '2', 'groups': '1'},
		{'username': 'guest', 'email': 'guest@localhost', 'password': '084e0343a0486ff05530df6c705c8bb4', 'role': '4', 'groups': '1'}
	]

	try:
		if Role.get(Role.name == 'superAdmin').role_id == 1:
			create_users = False
		else:
			create_users = True
	except Exception:
		create_users = True

	try:
		if create_users:
			User.insert_many(data_source).on_conflict_ignore().execute()
	except Exception as e:
		print(str(e))

	data_source = [
		{'user_id': '1', 'user_group_id': '1', 'user_role_id': '1'},
		{'user_id': '2', 'user_group_id': '1', 'user_role_id': '2'},
		{'user_id': '3', 'user_group_id': '1', 'user_role_id': '4'}
	]

	try:
		if create_users:
			UserGroups.insert_many(data_source).on_conflict_ignore().execute()
	except Exception as e:
		print(str(e))

	data_source = [
		{'name': 'superAdmin', 'description': 'Has the highest level of administrative permissions and controls the actions of all other users'},
		{'name': 'admin', 'description': 'Has access everywhere except the Admin area'},
		{'name': 'user', 'description': 'Has the same rights as the admin but has no access to the Servers page'},
		{'name': 'guest', 'description': 'Read-only access'}
	]

	try:
		Role.insert_many(data_source).on_conflict_ignore().execute()
	except Exception as e:
		print(str(e))

	try:
		Groups.insert(name='Default', description='All servers are included in this group by default', group_id=1).on_conflict_ignore().execute()
	except Exception as e:
		print(str(e))

	data_source = [
		{'service_id': 1, 'service': 'HAProxy', 'slug': 'haproxy'},
		{'service_id': 2, 'service': 'NGINX', 'slug': 'nginx'},
		{'service_id': 3, 'service': 'Keepalived', 'slug': 'keepalived'},
		{'service_id': 4, 'service': 'Apache', 'slug': 'apache'},
		{'service_id': 5, 'service': 'HA cluster', 'slug': 'cluster'},
		{'service_id': 6, 'service': 'UDP listener', 'slug': 'udp'},
	]

	try:
		Services.insert_many(data_source).on_conflict_ignore().execute()
	except Exception:
		Services.drop_table()
		Services.create_table()
		try:
			Services.insert_many(data_source).on_conflict_ignore().execute()
		except Exception as e:
			print(str(e))

	data_source = [
		{'code': 'RW', 'name': 'Rwanda'},
		{'code': 'SO', 'name': 'Somalia'},
		{'code': 'YE', 'name': 'Yemen'},
		{'code': 'IQ', 'name': 'Iraq'},
		{'code': 'SA', 'name': 'Saudi Arabia'},
		{'code': 'IR', 'name': 'Iran'},
		{'code': 'CY', 'name': 'Cyprus'},
		{'code': 'TZ', 'name': 'Tanzania'},
		{'code': 'SY', 'name': 'Syria'},
		{'code': 'AM', 'name': 'Armenia'},
		{'code': 'KE', 'name': 'Kenya'},
		{'code': 'CD', 'name': 'DR Congo'},
		{'code': 'DJ', 'name': 'Djibouti'},
		{'code': 'UG', 'name': 'Uganda'},
		{'code': 'CF', 'name': 'Central African Republic'},
		{'code': 'SC', 'name': 'Seychelles'},
		{'code': 'JO', 'name': 'Hashemite Kingdom of Jordan'},
		{'code': 'LB', 'name': 'Lebanon'},
		{'code': 'KW', 'name': 'Kuwait'},
		{'code': 'OM', 'name': 'Oman'},
		{'code': 'QA', 'name': 'Qatar'},
		{'code': 'BH', 'name': 'Bahrain'},
		{'code': 'AE', 'name': 'United Arab Emirates'},
		{'code': 'IL', 'name': 'Israel'},
		{'code': 'TR', 'name': 'Turkey'},
		{'code': 'ET', 'name': 'Ethiopia'},
		{'code': 'ER', 'name': 'Eritrea'},
		{'code': 'EG', 'name': 'Egypt'},
		{'code': 'SD', 'name': 'Sudan'},
		{'code': 'GR', 'name': 'Greece'},
		{'code': 'BI', 'name': 'Burundi'},
		{'code': 'EE', 'name': 'Estonia'},
		{'code': 'LV', 'name': 'Latvia'},
		{'code': 'AZ', 'name': 'Azerbaijan'},
		{'code': 'LT', 'name': 'Republic of Lithuania'},
		{'code': 'SJ', 'name': 'Svalbard and Jan Mayen'},
		{'code': 'GE', 'name': 'Georgia'},
		{'code': 'MD', 'name': 'Republic of Moldova'},
		{'code': 'BY', 'name': 'Belarus'},
		{'code': 'FI', 'name': 'Finland'},
		{'code': 'AX', 'name': 'Åland'},
		{'code': 'UA', 'name': 'Ukraine'},
		{'code': 'MK', 'name': 'North Macedonia'},
		{'code': 'HU', 'name': 'Hungary'},
		{'code': 'BG', 'name': 'Bulgaria'},
		{'code': 'AL', 'name': 'Albania'},
		{'code': 'PL', 'name': 'Poland'},
		{'code': 'RO', 'name': 'Romania'},
		{'code': 'XK', 'name': 'Kosovo'},
		{'code': 'ZW', 'name': 'Zimbabwe'},
		{'code': 'ZM', 'name': 'Zambia'},
		{'code': 'KM', 'name': 'Comoros'},
		{'code': 'MW', 'name': 'Malawi'},
		{'code': 'LS', 'name': 'Lesotho'},
		{'code': 'BW', 'name': 'Botswana'},
		{'code': 'MU', 'name': 'Mauritius'},
		{'code': 'SZ', 'name': 'Eswatini'},
		{'code': 'RE', 'name': 'Réunion'},
		{'code': 'ZA', 'name': 'South Africa'},
		{'code': 'YT', 'name': 'Mayotte'},
		{'code': 'MZ', 'name': 'Mozambique'},
		{'code': 'MG', 'name': 'Madagascar'},
		{'code': 'AF', 'name': 'Afghanistan'},
		{'code': 'PK', 'name': 'Pakistan'},
		{'code': 'BD', 'name': 'Bangladesh'},
		{'code': 'TM', 'name': 'Turkmenistan'},
		{'code': 'TJ', 'name': 'Tajikistan'},
		{'code': 'LK', 'name': 'Sri Lanka'},
		{'code': 'BT', 'name': 'Bhutan'},
		{'code': 'IN', 'name': 'India'},
		{'code': 'MV', 'name': 'Maldives'},
		{'code': 'IO', 'name': 'British Indian Ocean Territory'},
		{'code': 'NP', 'name': 'Nepal'},
		{'code': 'MM', 'name': 'Myanmar'},
		{'code': 'UZ', 'name': 'Uzbekistan'},
		{'code': 'KZ', 'name': 'Kazakhstan'},
		{'code': 'KG', 'name': 'Kyrgyzstan'},
		{'code': 'TF', 'name': 'French Southern Territories'},
		{'code': 'HM', 'name': 'Heard Island and McDonald Islands'},
		{'code': 'CC', 'name': 'Cocos [Keeling] Islands'},
		{'code': 'PW', 'name': 'Palau'},
		{'code': 'VN', 'name': 'Vietnam'},
		{'code': 'TH', 'name': 'Thailand'},
		{'code': 'ID', 'name': 'Indonesia'},
		{'code': 'LA', 'name': 'Laos'},
		{'code': 'TW', 'name': 'Taiwan'},
		{'code': 'PH', 'name': 'Philippines'},
		{'code': 'MY', 'name': 'Malaysia'},
		{'code': 'CN', 'name': 'China'},
		{'code': 'HK', 'name': 'Hong Kong'},
		{'code': 'BN', 'name': 'Brunei'},
		{'code': 'MO', 'name': 'Macao'},
		{'code': 'KH', 'name': 'Cambodia'},
		{'code': 'KR', 'name': 'South Korea'},
		{'code': 'JP', 'name': 'Japan'},
		{'code': 'KP', 'name': 'North Korea'},
		{'code': 'SG', 'name': 'Singapore'},
		{'code': 'CK', 'name': 'Cook Islands'},
		{'code': 'TL', 'name': 'East Timor'},
		{'code': 'RU', 'name': 'Russia'},
		{'code': 'MN', 'name': 'Mongolia'},
		{'code': 'AU', 'name': 'Australia'},
		{'code': 'CX', 'name': 'Christmas Island'},
		{'code': 'MH', 'name': 'Marshall Islands'},
		{'code': 'FM', 'name': 'Federated States of Micronesia'},
		{'code': 'PG', 'name': 'Papua New Guinea'},
		{'code': 'SB', 'name': 'Solomon Islands'},
		{'code': 'TV', 'name': 'Tuvalu'},
		{'code': 'NR', 'name': 'Nauru'},
		{'code': 'VU', 'name': 'Vanuatu'},
		{'code': 'NC', 'name': 'New Caledonia'},
		{'code': 'NF', 'name': 'Norfolk Island'},
		{'code': 'NZ', 'name': 'New Zealand'},
		{'code': 'FJ', 'name': 'Fiji'},
		{'code': 'LY', 'name': 'Libya'},
		{'code': 'CM', 'name': 'Cameroon'},
		{'code': 'SN', 'name': 'Senegal'},
		{'code': 'CG', 'name': 'Congo Republic'},
		{'code': 'PT', 'name': 'Portugal'},
		{'code': 'LR', 'name': 'Liberia'},
		{'code': 'CI', 'name': 'Ivory Coast'},
		{'code': 'GH', 'name': 'Ghana'},
		{'code': 'GQ', 'name': 'Equatorial Guinea'},
		{'code': 'NG', 'name': 'Nigeria'},
		{'code': 'BF', 'name': 'Burkina Faso'},
		{'code': 'TG', 'name': 'Togo'},
		{'code': 'GW', 'name': 'Guinea-Bissau'},
		{'code': 'MR', 'name': 'Mauritania'},
		{'code': 'BJ', 'name': 'Benin'},
		{'code': 'GA', 'name': 'Gabon'},
		{'code': 'SL', 'name': 'Sierra Leone'},
		{'code': 'ST', 'name': 'São Tomé and Príncipe'},
		{'code': 'GI', 'name': 'Gibraltar'},
		{'code': 'GM', 'name': 'Gambia'},
		{'code': 'GN', 'name': 'Guinea'},
		{'code': 'TD', 'name': 'Chad'},
		{'code': 'NE', 'name': 'Niger'},
		{'code': 'ML', 'name': 'Mali'},
		{'code': 'EH', 'name': 'Western Sahara'},
		{'code': 'TN', 'name': 'Tunisia'},
		{'code': 'ES', 'name': 'Spain'},
		{'code': 'MA', 'name': 'Morocco'},
		{'code': 'MT', 'name': 'Malta'},
		{'code': 'DZ', 'name': 'Algeria'},
		{'code': 'FO', 'name': 'Faroe Islands'},
		{'code': 'DK', 'name': 'Denmark'},
		{'code': 'IS', 'name': 'Iceland'},
		{'code': 'GB', 'name': 'United Kingdom'},
		{'code': 'CH', 'name': 'Switzerland'},
		{'code': 'SE', 'name': 'Sweden'},
		{'code': 'NL', 'name': 'Netherlands'},
		{'code': 'AT', 'name': 'Austria'},
		{'code': 'BE', 'name': 'Belgium'},
		{'code': 'DE', 'name': 'Germany'},
		{'code': 'LU', 'name': 'Luxembourg'},
		{'code': 'IE', 'name': 'Ireland'},
		{'code': 'MC', 'name': 'Monaco'},
		{'code': 'FR', 'name': 'France'},
		{'code': 'AD', 'name': 'Andorra'},
		{'code': 'LI', 'name': 'Liechtenstein'},
		{'code': 'JE', 'name': 'Jersey'},
		{'code': 'IM', 'name': 'Isle of Man'},
		{'code': 'GG', 'name': 'Guernsey'},
		{'code': 'SK', 'name': 'Slovakia'},
		{'code': 'CZ', 'name': 'Czechia'},
		{'code': 'NO', 'name': 'Norway'},
		{'code': 'VA', 'name': 'Vatican City'},
		{'code': 'SM', 'name': 'San Marino'},
		{'code': 'IT', 'name': 'Italy'},
		{'code': 'SI', 'name': 'Slovenia'},
		{'code': 'ME', 'name': 'Montenegro'},
		{'code': 'HR', 'name': 'Croatia'},
		{'code': 'BA', 'name': 'Bosnia and Herzegovina'},
		{'code': 'AO', 'name': 'Angola'},
		{'code': 'NA', 'name': 'Namibia'},
		{'code': 'SH', 'name': 'Saint Helena'},
		{'code': 'BV', 'name': 'Bouvet Island'},
		{'code': 'BB', 'name': 'Barbados'},
		{'code': 'CV', 'name': 'Cabo Verde'},
		{'code': 'GY', 'name': 'Guyana'},
		{'code': 'GF', 'name': 'French Guiana'},
		{'code': 'SR', 'name': 'Suriname'},
		{'code': 'PM', 'name': 'Saint Pierre and Miquelon'},
		{'code': 'GL', 'name': 'Greenland'},
		{'code': 'PY', 'name': 'Paraguay'},
		{'code': 'UY', 'name': 'Uruguay'},
		{'code': 'BR', 'name': 'Brazil'},
		{'code': 'FK', 'name': 'Falkland Islands'},
		{'code': 'GS', 'name': 'South Georgia and the South Sandwich Islands'},
		{'code': 'JM', 'name': 'Jamaica'},
		{'code': 'DO', 'name': 'Dominican Republic'},
		{'code': 'CU', 'name': 'Cuba'},
		{'code': 'MQ', 'name': 'Martinique'},
		{'code': 'BS', 'name': 'Bahamas'},
		{'code': 'BM', 'name': 'Bermuda'},
		{'code': 'AI', 'name': 'Anguilla'},
		{'code': 'TT', 'name': 'Trinidad and Tobago'},
		{'code': 'KN', 'name': 'St Kitts and Nevis'},
		{'code': 'DM', 'name': 'Dominica'},
		{'code': 'AG', 'name': 'Antigua and Barbuda'},
		{'code': 'LC', 'name': 'Saint Lucia'},
		{'code': 'TC', 'name': 'Turks and Caicos Islands'},
		{'code': 'AW', 'name': 'Aruba'},
		{'code': 'VG', 'name': 'British Virgin Islands'},
		{'code': 'VC', 'name': 'Saint Vincent and the Grenadines'},
		{'code': 'MS', 'name': 'Montserrat'},
		{'code': 'MF', 'name': 'Saint Martin'},
		{'code': 'BL', 'name': 'Saint Barthélemy'},
		{'code': 'GP', 'name': 'Guadeloupe'},
		{'code': 'GD', 'name': 'Grenada'},
		{'code': 'KY', 'name': 'Cayman Islands'},
		{'code': 'BZ', 'name': 'Belize'},
		{'code': 'SV', 'name': 'El Salvador'},
		{'code': 'GT', 'name': 'Guatemala'},
		{'code': 'HN', 'name': 'Honduras'},
		{'code': 'NI', 'name': 'Nicaragua'},
		{'code': 'CR', 'name': 'Costa Rica'},
		{'code': 'VE', 'name': 'Venezuela'},
		{'code': 'EC', 'name': 'Ecuador'},
		{'code': 'CO', 'name': 'Colombia'},
		{'code': 'PA', 'name': 'Panama'},
		{'code': 'HT', 'name': 'Haiti'},
		{'code': 'AR', 'name': 'Argentina'},
		{'code': 'CL', 'name': 'Chile'},
		{'code': 'BO', 'name': 'Bolivia'},
		{'code': 'PE', 'name': 'Peru'},
		{'code': 'MX', 'name': 'Mexico'},
		{'code': 'PF', 'name': 'French Polynesia'},
		{'code': 'PN', 'name': 'Pitcairn Islands'},
		{'code': 'KI', 'name': 'Kiribati'},
		{'code': 'TK', 'name': 'Tokelau'},
		{'code': 'TO', 'name': 'Tonga'},
		{'code': 'WF', 'name': 'Wallis and Futuna'},
		{'code': 'WS', 'name': 'Samoa'},
		{'code': 'NU', 'name': 'Niue'},
		{'code': 'MP', 'name': 'Northern Mariana Islands'},
		{'code': 'GU', 'name': 'Guam'},
		{'code': 'PR', 'name': 'Puerto Rico'},
		{'code': 'VI', 'name': 'U.S. Virgin Islands'},
		{'code': 'UM', 'name': 'U.S. Minor Outlying Islands'},
		{'code': 'AS', 'name': 'American Samoa'},
		{'code': 'CA', 'name': 'Canada'},
		{'code': 'US', 'name': 'United States'},
		{'code': 'PS', 'name': 'Palestine'},
		{'code': 'RS', 'name': 'Serbia'},
		{'code': 'AQ', 'name': 'Antarctica'},
		{'code': 'SX', 'name': 'Sint Maarten'},
		{'code': 'CW', 'name': 'Curaçao'},
		{'code': 'BQ', 'name': 'Bonaire'},
		{'code': 'SS', 'name': 'South Sudan'}
	]

	try:
		GeoipCodes.insert_many(data_source).on_conflict_ignore().execute()
	except Exception as e:
		print(str(e))

	data_source = [
		{'name': 'roxy-wi-metrics', 'current_version': '1.0', 'new_version': '0', 'is_roxy': 1, 'desc': ''},
		{'name': 'roxy-wi-checker', 'current_version': '1.0', 'new_version': '0', 'is_roxy': 1, 'desc': ''},
		{'name': 'roxy-wi-keep_alive', 'current_version': '1.0', 'new_version': '0', 'is_roxy': 1, 'desc': ''},
		{'name': 'roxy-wi-portscanner', 'current_version': '1.0', 'new_version': '0', 'is_roxy': 1, 'desc': ''},
		{'name': 'roxy-wi-socket', 'current_version': '1.0', 'new_version': '0', 'is_roxy': 1, 'desc': ''},
		{'name': 'roxy-wi-prometheus-exporter', 'current_version': '1.0', 'new_version': '0', 'is_roxy': 1, 'desc': ''},
		{'name': 'roxy-wi-smon', 'current_version': '1.0', 'new_version': '0', 'is_roxy': 1, 'desc': ''},
		{'name': 'prometheus', 'current_version': '1.0', 'new_version': '1.0', 'is_roxy': 0, 'desc': 'Prometheus service'},
		{'name': 'grafana-server', 'current_version': '1.0', 'new_version': '1.0', 'is_roxy': 0, 'desc': 'Grafana service'},
		{'name': 'fail2ban', 'current_version': '1.0', 'new_version': '1.0', 'is_roxy': 0, 'desc': 'Fail2ban service'},
		{'name': 'rabbitmq-server', 'current_version': '1.0', 'new_version': '1.0', 'is_roxy': 0, 'desc': 'Rabbitmq service'},
	]

	try:
		RoxyTool.insert_many(data_source).on_conflict_ignore().execute()
	except Exception as e:
		print(str(e))


# Needs for insert version in first time
def update_db_v_3_4_5_22():
	try:
		Version.insert(version='3.4.5.2').execute()
	except Exception as e:
		print('Cannot insert version %s' % e)


# Needs for updating user_group. Do not delete
def update_db_v_4_3_0():
	try:
		UserGroups.insert_from(
			User.select(User.user_id, User.groups), fields=[UserGroups.user_id, UserGroups.user_group_id]
		).on_conflict_ignore().execute()
	except Exception as e:
		if e.args[0] == 'duplicate column name: haproxy' or str(e) == '(1060, "Duplicate column name \'haproxy\'")':
			print('Updating... go to version 4.3.1')
		else:
			print("An error occurred:", e)


def update_db_v_6_3_13_1():
	try:
		SmonTcpCheck.insert_from(
			SMON.select(SMON.id, SMON.ip, SMON.port).where(
				(SMON.http == '') & (SMON.check_type == 'tcp')
			), fields=[SmonTcpCheck.smon_id, SmonTcpCheck.ip, SmonTcpCheck.port]
		).on_conflict_ignore().execute()
	except Exception as e:
		if e.args[0] == 'no such column: t1.name' or str(e) == 'type object \'SMON\' has no attribute \'ip\'':
			print('Updating... DB has been updated to version 6.3.13-1')
		else:
			print("An error occurred:", e)


def update_db_v_6_3_13_2():
	query = SMON.select().where(SMON.http != '')
	try:
		query_res = query.execute()
	except Exception as e:
		print("An error occurred:", e)
	else:
		for i in query_res:
			try:
				proto = i.http.split(':')[0]
				uri = i.http.split(':')[1]
			except Exception:
				proto = ''
				uri = ''
			url = f'{proto}://{i.name}:{i.port}{uri}'
			SmonHttpCheck.insert(smon_id=i.id, url=url, body=i.body).on_conflict_ignore().execute()


def update_db_v_6_3_13_3():
	try:
		SmonPingCheck.insert_from(
			SMON.select(SMON.id, SMON.ip).where(SMON.check_type == 'ping'), fields=[SmonPingCheck.smon_id, SmonPingCheck.ip]
		).on_conflict_ignore().execute()
	except Exception as e:
		if e.args[0] == 'duplicate column name: haproxy' or str(e) == 'type object \'SMON\' has no attribute \'ip\'':
			print('Updating... DB has been updated to version 6.3.13-2')
		else:
			print("An error occurred:", e)


def update_db_v_6_3_13_4():
	try:
		migrate(
			migrator.alter_column_type('smon', 'time_state', DateTimeField()),
			migrator.rename_column('smon', 'ip', 'name'),
			migrator.drop_column('smon', 'script', cascade=False),
			migrator.drop_column('smon', 'http_status', cascade=False),
		)
	except Exception as e:
		if e.args[0] == 'duplicate column name: check_type' or str(e) == '(1091, "Can\'t DROP COLUMN `script`; check that it exists")':
			print('Updating... DB has been updated to version 6.3.13-3')
		elif e.args[0] == 'duplicate column name: check_type' or str(e) == '(1091, "Can\'t DROP COLUMN `http_status`; check that it exists")':
			print('Updating... DB has been updated to version 6.3.13-3')
		elif e.args[0] == 'table smon__tmp__ has no column named UNIQUE' or str(e) == "'bool' object has no attribute 'sql'":
			print('Updating... DB has been updated to version 6.3.13-3')
		else:
			print("An error occurred:", e)


def update_db_v_6_3_13_5():
	try:
		SMON.update(check_type='http').where(SMON.http != '').execute()
	except Exception as e:
		print("An error occurred:", e)


def update_db_v_6_3_17():
	try:
		Setting.delete().where(Setting.param == 'lists_path').execute()
	except Exception as e:
		print("An error occurred:", e)
	else:
		print("Updating... DB has been updated to version 6.3.17")


def update_db_v_6_3_18():
	try:
		Setting.delete().where(Setting.param == 'ssl_local_path').execute()
	except Exception as e:
		print("An error occurred:", e)
	else:
		print("Updating... DB has been updated to version 6.3.18")


def update_db_v_7_1_2():
	try:
		Setting.delete().where(Setting.param == 'stats_user').execute()
		Setting.delete().where(Setting.param == 'stats_password').execute()
		Setting.delete().where(Setting.param == 'stats_port').execute()
		Setting.delete().where(Setting.param == 'stats_page').execute()
	except Exception as e:
		print("An error occurred:", e)
	else:
		print("Updating... DB has been updated to version 7.1.2")


def update_db_v_7_1_2_1():
	try:
		migrate(
			migrator.add_column('cred', 'passphrase', CharField(null=True))
		)
	except Exception as e:
		if e.args[0] == 'duplicate column name: passphrase' or str(e) == '(1060, "Duplicate column name \'passphrase\'")':
			print('Updating... DB has been updated to version 7.1.2-1')
		else:
			print("An error occurred:", e)


def update_db_v_7_2_0():
	try:
		if mysql_enable:
			migrate(
				migrator.add_column('smon_ping_check', 'interval', IntegerField(default=120)),
				migrator.add_column('smon_http_check', 'interval', IntegerField(default=120)),
				migrator.add_column('smon_tcp_check', 'interval', IntegerField(default=120)),
				migrator.add_column('smon_dns_check', 'interval', IntegerField(default=120)),
				migrator.add_column('smon_ping_check', 'agent_id', IntegerField(default=1)),
				migrator.add_column('smon_http_check', 'agent_id', IntegerField(default=1)),
				migrator.add_column('smon_tcp_check', 'agent_id', IntegerField(default=1)),
				migrator.add_column('smon_dns_check', 'agent_id', IntegerField(default=1))
			)
		else:
			migrate(
				migrator.add_column('smon_ping_check', 'interval', IntegerField(constraints=[SQL('DEFAULT 120')])),
				migrator.add_column('smon_http_check', 'interval', IntegerField(constraints=[SQL('DEFAULT 120')])),
				migrator.add_column('smon_tcp_check', 'interval', IntegerField(constraints=[SQL('DEFAULT 120')])),
				migrator.add_column('smon_dns_check', 'interval', IntegerField(constraints=[SQL('DEFAULT 120')])),
				migrator.add_column('smon_ping_check', 'agent_id', IntegerField(constraints=[SQL('DEFAULT 1')])),
				migrator.add_column('smon_http_check', 'agent_id', IntegerField(constraints=[SQL('DEFAULT 1')])),
				migrator.add_column('smon_tcp_check', 'agent_id', IntegerField(constraints=[SQL('DEFAULT 1')])),
				migrator.add_column('smon_dns_check', 'agent_id', IntegerField(constraints=[SQL('DEFAULT 1')]))
			)
	except Exception as e:
		if e.args[0] == 'duplicate column name: agent_id' or str(e) == '(1060, "Duplicate column name \'agent_id\'")':
			print('Updating... DB has been updated to version 7.2.0')
		elif e.args[0] == 'duplicate column name: interval' or str(e) == '(1060, "Duplicate column name \'interval\'")':
			print('Updating... DB has been updated to version 7.2.0')
		else:
			print("An error occurred:", e)


def update_db_v_7_2_0_1():
	try:
		Setting.delete().where(Setting.param == 'smon_check_interval').execute()
		Setting.delete().where((Setting.param == 'smon_keep_history_range') & (Setting.section == 'monitoring')).execute()
		Setting.delete().where((Setting.param == 'smon_ssl_expire_warning_alert') & (Setting.section == 'monitoring')).execute()
		Setting.delete().where((Setting.param == 'smon_ssl_expire_critical_alert') & (Setting.section == 'monitoring')).execute()
	except Exception as e:
		print("An error occurred:", e)
	else:
		print("Updating... DB has been updated to version 7.2.0-1")


def update_db_v_7_2_3():
	try:
		if mysql_enable:
			migrate(
				migrator.add_column('checker_setting', 'mm_id', IntegerField(default=0)),
				migrator.add_column('smon', 'mm_channel_id', IntegerField(default=0)),
			)
		else:
			migrate(
				migrator.add_column('checker_setting', 'mm_id', IntegerField(constraints=[SQL('DEFAULT 0')])),
				migrator.add_column('smon', 'mm_channel_id', IntegerField(constraints=[SQL('DEFAULT 0')])),
			)
	except Exception as e:
		if e.args[0] == 'duplicate column name: mm_id' or str(e) == '(1060, "Duplicate column name \'mm_id\'")':
			print('Updating... DB has been updated to version 7.2.3')
		else:
			print("An error occurred:", e)


def update_db_v_7_3_1():
	try:
		if mysql_enable:
			migrate(
				migrator.add_column('ha_cluster_vips', 'use_src', IntegerField(default=0)),
			)
		else:
			migrate(
				migrator.add_column('ha_cluster_vips', 'use_src', IntegerField(constraints=[SQL('DEFAULT 0')])),
			)
	except Exception as e:
		if e.args[0] == 'duplicate column name: use_src' or str(e) == '(1060, "Duplicate column name \'use_src\'")':
			print('Updating... DB has been updated to version 7.3.1')
		else:
			print("An error occurred:", e)


def update_ver():
	try:
		Version.update(version='7.3.3.0').execute()
	except Exception:
		print('Cannot update version')


def check_ver():
	try:
		ver = Version.get()
	except Exception as e:
		print(str(e))
	else:
		return ver.version


def update_all():
	if check_ver() is None:
		update_db_v_3_4_5_22()
	update_db_v_4_3_0()
	update_db_v_6_3_13_1()
	update_db_v_6_3_13_2()
	update_db_v_6_3_13_3()
	update_db_v_6_3_13_4()
	update_db_v_6_3_13_5()
	update_db_v_6_3_17()
	update_db_v_6_3_18()
	update_db_v_7_1_2()
	update_db_v_7_1_2_1()
	update_db_v_7_2_0()
	update_db_v_7_2_0_1()
	update_db_v_7_2_3()
	update_db_v_7_3_1()
	update_ver()


if __name__ == "__main__":
	create_tables()
	default_values()
	update_all()
