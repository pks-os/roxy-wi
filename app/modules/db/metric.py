from typing import Literal

from app.modules.db.db_model import connect, mysql_enable, Metrics, MetricsHttpStatus, Server, NginxMetrics, ApacheMetrics, WafMetrics
from app.modules.db.common import out_error
import app.modules.roxy_wi_tools as roxy_wi_tools

MODELS = {
	'haproxy': Metrics,
	'nginx': NginxMetrics,
	'apache': ApacheMetrics,
	'http': MetricsHttpStatus,
	'waf': WafMetrics
}


def insert_service_metrics(service: Literal['haproxy', 'nginx', 'apache', 'waf', 'http'], **kwargs):
	get_date = roxy_wi_tools.GetDate()
	cur_date = get_date.return_date('regular')
	kwargs['date'] = cur_date
	model = MODELS[service]
	try:
		model.insert(**kwargs).execute()
	except Exception as e:
		out_error(e)


def delete_service_metrics(service: Literal['haproxy', 'http', 'waf', 'nginx', 'apache']) -> None:
	get_date = roxy_wi_tools.GetDate()
	cur_date = get_date.return_date('regular', timedelta_minus=3)
	model = MODELS[service]
	try:
		model.delete().where(model.date < cur_date).execute()
	except Exception as e:
		out_error(e)


def select_metrics(serv, service, **kwargs):
	conn = connect()
	cursor = conn.cursor()

	if service in ('nginx', 'apache', 'waf'):
		metrics_table = '{}_metrics'.format(service)
	elif service == 'http_metrics':
		metrics_table = 'metrics_http_status'
	else:
		metrics_table = 'metrics'

	if mysql_enable == '1':
		if kwargs.get('time_range') == '60':
			date_from = "and date > CONVERT_TZ(NOW(),'SYSTEM','+0:00') - INTERVAL 60 minute group by `date` div 100"
		elif kwargs.get('time_range') == '180':
			date_from = "and date > CONVERT_TZ(NOW(),'SYSTEM','+0:00') - INTERVAL 180 minute group by `date` div 200"
		elif kwargs.get('time_range') == '360':
			date_from = "and date > CONVERT_TZ(NOW(),'SYSTEM','+0:00') - INTERVAL 360 minute group by `date` div 300"
		elif kwargs.get('time_range') == '720':
			date_from = "and date > CONVERT_TZ(NOW(),'SYSTEM','+0:00') - INTERVAL 720 minute group by `date` div 500"
		elif kwargs.get('time_range') == '1':
			date_from = "and date > CONVERT_TZ(NOW(),'SYSTEM','+0:00') - INTERVAL 1 minute"
		else:
			date_from = "and date > CONVERT_TZ(NOW(),'SYSTEM','+0:00') - INTERVAL 30 minute"
		sql = """ select * from {metrics_table} where serv = '{serv}' {date_from} order by `date` asc """.format(
			metrics_table=metrics_table, serv=serv, date_from=date_from
		)
	else:
		if kwargs.get('time_range') == '60':
			date_from = "and date > datetime('now', '-60 minutes', 'UTC') and rowid % 2 = 0"
		elif kwargs.get('time_range') == '180':
			date_from = "and date > datetime('now', '-180 minutes', 'UTC') and rowid % 5 = 0"
		elif kwargs.get('time_range') == '360':
			date_from = "and date > datetime('now', '-360 minutes', 'UTC') and rowid % 7 = 0"
		elif kwargs.get('time_range') == '720':
			date_from = "and date > datetime('now', '-720 minutes', 'UTC') and rowid % 9 = 0"
		elif kwargs.get('time_range') == '1':
			date_from = "and date > datetime('now', '-1 minutes', 'UTC')"
		else:
			date_from = "and date > datetime('now', '-30 minutes', 'UTC')"

		sql = """ select * from (select * from {metrics_table} where serv = '{serv}' {date_from} order by `date`) order by `date` """.format(
			metrics_table=metrics_table, serv=serv, date_from=date_from)

	try:
		cursor.execute(sql)
	except Exception as e:
		out_error(e)
	else:
		return cursor.fetchall()


def select_servers_metrics_for_master(group_id: int):
	query = Server.select(Server.ip).where(
		((Server.haproxy_metrics == 1) | (Server.nginx_metrics == 1) | (Server.apache_metrics == 1))
		& (Server.group_id == group_id)
	)

	try:
		return query.execute()
	except Exception as e:
		out_error(e)


def select_metrics_enabled(service: Literal['haproxy', 'nginx', 'apache']):
	query_where = {
		'haproxy': ((Server.haproxy_metrics == 1) & (Server.haproxy == 1)),
		'nginx': ((Server.nginx_metrics == 1) & (Server.nginx == 1)),
		'apache': ((Server.apache_metrics == 1) & (Server.apache == 1)),
	}
	try:
		return Server.select(Server.ip).where(query_where[service] & (Server.enabled == 1)).execute()
	except Exception as e:
		out_error(e)


def select_table_metrics(group_id):
	conn = connect()
	cursor = conn.cursor()

	if group_id == 1:
		groups = ""
	else:
		groups = "and servers.group_id = '{group}' ".format(group=group_id)
	if mysql_enable == '1':
		sql = """
				select ip.ip, hostname, avg_sess_1h, avg_sess_24h, avg_sess_3d, max_sess_1h, max_sess_24h, max_sess_3d,
				avg_cur_1h, avg_cur_24h, avg_cur_3d, max_con_1h, max_con_24h, max_con_3d from
				(select servers.ip from servers where haproxy_metrics = 1 ) as ip,

				(select servers.ip, servers.hostname as hostname from servers left join metrics as metr on servers.ip = metr.serv where servers.haproxy_metrics = 1 %s) as hostname,

				(select servers.ip,round(avg(metr.sess_rate), 1) as avg_sess_1h from servers
				left join metrics as metr on metr.serv = servers.ip
				where servers.haproxy_metrics = 1 and
				metr.date <= now() and metr.date >= DATE_ADD(NOW(), INTERVAL -1 HOUR)
				group by servers.ip)   as avg_sess_1h,

				(select servers.ip,round(avg(metr.sess_rate), 1) as avg_sess_24h from servers
				left join metrics as metr on metr.serv = servers.ip
				where servers.haproxy_metrics = 1 and
				metr.date <= now() and metr.date >= DATE_ADD(NOW(),INTERVAL -24 HOUR)
				group by servers.ip) as avg_sess_24h,

				(select servers.ip,round(avg(metr.sess_rate), 1) as avg_sess_3d from servers
				left join metrics as metr on metr.serv = servers.ip
				where servers.haproxy_metrics = 1 and
				metr.date <= now() and metr.date >= DATE_ADD(NOW(), INTERVAL -3 DAY)
				group by servers.ip ) as avg_sess_3d,

		(select servers.ip,max(metr.sess_rate) as max_sess_1h from servers
				left join metrics as metr on metr.serv = servers.ip
				where servers.haproxy_metrics = 1 and
				metr.date <= now() and metr.date >= DATE_ADD(NOW(),INTERVAL -1 HOUR)
				group by servers.ip)   as max_sess_1h,

				(select servers.ip,max(metr.sess_rate) as max_sess_24h from servers
				left join metrics as metr on metr.serv = servers.ip
				where servers.haproxy_metrics = 1 and
				metr.date <= now() and metr.date >= DATE_ADD(NOW(),INTERVAL -24 HOUR)
				group by servers.ip) as max_sess_24h,

				(select servers.ip,max(metr.sess_rate) as max_sess_3d from servers
				left join metrics as metr on metr.serv = servers.ip
				where servers.haproxy_metrics = 1 and
				metr.date <=  now() and metr.date >= DATE_ADD(NOW(),INTERVAL -3 DAY)
				group by servers.ip ) as max_sess_3d,

				(select servers.ip,round(avg(metr.curr_con+metr.cur_ssl_con), 1) as avg_cur_1h from servers
				left join metrics as metr on metr.serv = servers.ip
				where servers.haproxy_metrics = 1 and
				metr.date <= now() and metr.date >= DATE_ADD(NOW(),INTERVAL -1 HOUR)
				group by servers.ip)   as avg_cur_1h,

				(select servers.ip,round(avg(metr.curr_con+metr.cur_ssl_con), 1) as avg_cur_24h from servers
				left join metrics as metr on metr.serv = servers.ip
				where servers.haproxy_metrics = 1 and
				metr.date <= now() and metr.date >= DATE_ADD(NOW(),INTERVAL -24 HOUR)
				group by servers.ip) as avg_cur_24h,

		(select servers.ip,round(avg(metr.curr_con+metr.cur_ssl_con), 1) as avg_cur_3d from servers
		left join metrics as metr on metr.serv = servers.ip
		where servers.haproxy_metrics = 1 and
		metr.date <=  now() and metr.date >= DATE_ADD(NOW(),INTERVAL -3 DAY)
		group by servers.ip ) as avg_cur_3d,

		(select servers.ip,max(metr.curr_con) as max_con_1h from servers
				left join metrics as metr on metr.serv = servers.ip
				where servers.haproxy_metrics = 1 and
				metr.date <= now() and metr.date >= DATE_ADD(NOW(),INTERVAL -1 HOUR)
				group by servers.ip)   as max_con_1h,

				(select servers.ip,max(metr.curr_con) as max_con_24h from servers
				left join metrics as metr on metr.serv = servers.ip
				where servers.haproxy_metrics = 1 and
				metr.date <= now() and metr.date >= DATE_ADD(NOW(),INTERVAL -24 HOUR)
				group by servers.ip) as max_con_24h,

				(select servers.ip,max(metr.curr_con) as max_con_3d from servers
				left join metrics as metr on metr.serv = servers.ip
				where servers.haproxy_metrics = 1 and
				metr.date <= now() and metr.date >= DATE_ADD(NOW(),INTERVAL -3 DAY)
				group by servers.ip ) as max_con_3d

		where ip.ip=hostname.ip
				and ip.ip=avg_sess_1h.ip
				and ip.ip=avg_sess_24h.ip
				and ip.ip=avg_sess_3d.ip
				and ip.ip=max_sess_1h.ip
				and ip.ip=max_sess_24h.ip
				and ip.ip=max_sess_3d.ip
				and ip.ip=avg_cur_1h.ip
				and ip.ip=avg_cur_24h.ip
				and ip.ip=avg_cur_3d.ip
				and ip.ip=max_con_1h.ip
				and ip.ip=max_con_24h.ip
				and ip.ip=max_con_3d.ip

				group by hostname.ip """ % groups
	else:
		sql = """
		select ip.ip, hostname, avg_sess_1h, avg_sess_24h, avg_sess_3d, max_sess_1h, max_sess_24h, max_sess_3d, avg_cur_1h,
			avg_cur_24h, avg_cur_3d, max_con_1h, max_con_24h, max_con_3d from
		(select servers.ip from servers where haproxy_metrics = 1 ) as ip,

		(select servers.ip, servers.hostname as hostname from servers left join metrics as metr on servers.ip = metr.serv where servers.haproxy_metrics = 1 %s) as hostname,

		(select servers.ip,round(avg(metr.sess_rate), 1) as avg_sess_1h from servers
		left join metrics as metr on metr.serv = servers.ip
		where servers.haproxy_metrics = 1 and
		metr.date <= datetime('now', 'localtime') and metr.date >= datetime('now', '-1 hours', 'localtime')
		group by servers.ip)   as avg_sess_1h,

		(select servers.ip,round(avg(metr.sess_rate), 1) as avg_sess_24h from servers
		left join metrics as metr on metr.serv = servers.ip
		where servers.haproxy_metrics = 1 and
		metr.date <= datetime('now', 'localtime') and metr.date >= datetime('now', '-24 hours', 'localtime')
		group by servers.ip) as avg_sess_24h,

		(select servers.ip,round(avg(metr.sess_rate), 1) as avg_sess_3d from servers
		left join metrics as metr on metr.serv = servers.ip
		where servers.haproxy_metrics = 1 and
		metr.date <= datetime('now', 'localtime') and metr.date >= datetime('now', '-3 days', 'localtime')
		group by servers.ip ) as avg_sess_3d,

		(select servers.ip,max(metr.sess_rate) as max_sess_1h from servers
		left join metrics as metr on metr.serv = servers.ip
		where servers.haproxy_metrics = 1 and
		metr.date <= datetime('now', 'localtime') and metr.date >= datetime('now', '-1 hours', 'localtime')
		group by servers.ip)   as max_sess_1h,

		(select servers.ip,max(metr.sess_rate) as max_sess_24h from servers
		left join metrics as metr on metr.serv = servers.ip
		where servers.haproxy_metrics = 1 and
		metr.date <= datetime('now', 'localtime') and metr.date >= datetime('now', '-24 hours', 'localtime')
		group by servers.ip) as max_sess_24h,

		(select servers.ip,max(metr.sess_rate) as max_sess_3d from servers
		left join metrics as metr on metr.serv = servers.ip
		where servers.haproxy_metrics = 1 and
		metr.date <= datetime('now', 'localtime') and metr.date >= datetime('now', '-3 days', 'localtime')
		group by servers.ip ) as max_sess_3d,

		(select servers.ip,round(avg(metr.curr_con+metr.cur_ssl_con), 1) as avg_cur_1h from servers
		left join metrics as metr on metr.serv = servers.ip
		where servers.haproxy_metrics = 1 and
		metr.date <= datetime('now', 'localtime') and metr.date >= datetime('now', '-1 hours', 'localtime')
		group by servers.ip)   as avg_cur_1h,

		(select servers.ip,round(avg(metr.curr_con+metr.cur_ssl_con), 1) as avg_cur_24h from servers
		left join metrics as metr on metr.serv = servers.ip
		where servers.haproxy_metrics = 1 and
		metr.date <= datetime('now', 'localtime') and metr.date >= datetime('now', '-24 hours', 'localtime')
		group by servers.ip) as avg_cur_24h,

		(select servers.ip,round(avg(metr.curr_con+metr.cur_ssl_con), 1) as avg_cur_3d from servers
		left join metrics as metr on metr.serv = servers.ip
		where servers.haproxy_metrics = 1 and
		metr.date <= datetime('now', 'localtime') and metr.date >= datetime('now', '-3 days', 'localtime')
		group by servers.ip ) as avg_cur_3d,

		(select servers.ip,max(metr.curr_con) as max_con_1h from servers
		left join metrics as metr on metr.serv = servers.ip
		where servers.haproxy_metrics = 1 and
		metr.date <= datetime('now', 'localtime') and metr.date >= datetime('now', '-1 hours', 'localtime')
		group by servers.ip)   as max_con_1h,

		(select servers.ip,max(metr.curr_con) as max_con_24h from servers
		left join metrics as metr on metr.serv = servers.ip
		where servers.haproxy_metrics = 1 and
		metr.date <= datetime('now', 'localtime') and metr.date >= datetime('now', '-24 hours', 'localtime')
		group by servers.ip) as max_con_24h,

		(select servers.ip,max(metr.curr_con) as max_con_3d from servers
		left join metrics as metr on metr.serv = servers.ip
		where servers.haproxy_metrics = 1 and
		metr.date <= datetime('now', 'localtime') and metr.date >= datetime('now', '-3 days', 'localtime')
		group by servers.ip ) as max_con_3d

		where ip.ip=hostname.ip
		and ip.ip=avg_sess_1h.ip
		and ip.ip=avg_sess_24h.ip
		and ip.ip=avg_sess_3d.ip
		and ip.ip=max_sess_1h.ip
		and ip.ip=max_sess_24h.ip
		and ip.ip=max_sess_3d.ip
		and ip.ip=avg_cur_1h.ip
		and ip.ip=avg_cur_24h.ip
		and ip.ip=avg_cur_3d.ip
		and ip.ip=max_con_1h.ip
		and ip.ip=max_con_24h.ip
		and ip.ip=max_con_3d.ip

		group by hostname.ip """ % groups

	try:
		cursor.execute(sql)
	except Exception as e:
		out_error(e)
	else:
		return cursor.fetchall()


def select_service_table_metrics(service: str, group_id: int):
	conn = connect()
	cursor = conn.cursor()

	if service in ('nginx', 'apache'):
		metrics_table = f'{service}_metrics'

	if group_id == 1:
		groups = ""
	else:
		groups = f"and servers.group_id = '{group_id}' "

	if mysql_enable == '1':
		sql = """
				select ip.ip, hostname, avg_cur_1h, avg_cur_24h, avg_cur_3d, max_con_1h, max_con_24h, max_con_3d from
				(select servers.ip from servers where {metrics} = 1 ) as ip,

				(select servers.ip, servers.hostname as hostname from servers left join {metrics} as metr on servers.ip = metr.serv where servers.{metrics} = 1 {groups}) as hostname,

				(select servers.ip,round(avg(metr.conn), 1) as avg_cur_1h from servers
				left join {metrics} as metr on metr.serv = servers.ip
				where servers.{metrics} = 1 and
				metr.date <= now() and metr.date >= DATE_ADD(NOW(),INTERVAL -1 HOUR)
				group by servers.ip)   as avg_cur_1h,

				(select servers.ip,round(avg(metr.conn), 1) as avg_cur_24h from servers
				left join {metrics} as metr on metr.serv = servers.ip
				where servers.{metrics} = 1 and
				metr.date <= now() and metr.date >= DATE_ADD(NOW(),INTERVAL -24 HOUR)
				group by servers.ip) as avg_cur_24h,

		(select servers.ip,round(avg(metr.conn), 1) as avg_cur_3d from servers
		left join {metrics} as metr on metr.serv = servers.ip
		where servers.{metrics} = 1 and
		metr.date <=  now() and metr.date >= DATE_ADD(NOW(),INTERVAL -3 DAY)
		group by servers.ip ) as avg_cur_3d,

		(select servers.ip,max(metr.conn) as max_con_1h from servers
				left join {metrics} as metr on metr.serv = servers.ip
				where servers.{metrics} = 1 and
				metr.date <= now() and metr.date >= DATE_ADD(NOW(),INTERVAL -1 HOUR)
				group by servers.ip)   as max_con_1h,

				(select servers.ip,max(metr.conn) as max_con_24h from servers
				left join {metrics} as metr on metr.serv = servers.ip
				where servers.{metrics} = 1 and
				metr.date <= now() and metr.date >= DATE_ADD(NOW(),INTERVAL -24 HOUR)
				group by servers.ip) as max_con_24h,

				(select servers.ip,max(metr.conn) as max_con_3d from servers
				left join {metrics} as metr on metr.serv = servers.ip
				where servers.{metrics} = 1 and
				metr.date <= now() and metr.date >= DATE_ADD(NOW(),INTERVAL -3 DAY)
				group by servers.ip ) as max_con_3d

		where ip.ip=hostname.ip
				and ip.ip=avg_cur_1h.ip
				and ip.ip=avg_cur_24h.ip
				and ip.ip=avg_cur_3d.ip
				and ip.ip=max_con_1h.ip
				and ip.ip=max_con_24h.ip
				and ip.ip=max_con_3d.ip

				group by hostname.ip """.format(metrics=metrics_table, groups=groups)
	else:
		sql = """
		select ip.ip, hostname, avg_cur_1h, avg_cur_24h, avg_cur_3d, max_con_1h, max_con_24h, max_con_3d from
		(select servers.ip from servers where {metrics} = 1 ) as ip,

		(select servers.ip, servers.hostname as hostname from servers left join {metrics} as metr on servers.ip = metr.serv where servers.{metrics} = 1 {groups}) as hostname,

		(select servers.ip,round(avg(metr.conn), 1) as avg_cur_1h from servers
		left join {metrics} as metr on metr.serv = servers.ip
		where servers.{metrics} = 1 and
		metr.date <= datetime('now', 'localtime') and metr.date >= datetime('now', '-1 hours', 'localtime')
		group by servers.ip)   as avg_cur_1h,

		(select servers.ip,round(avg(metr.conn), 1) as avg_cur_24h from servers
		left join {metrics} as metr on metr.serv = servers.ip
		where servers.{metrics} = 1 and
		metr.date <= datetime('now', 'localtime') and metr.date >= datetime('now', '-24 hours', 'localtime')
		group by servers.ip) as avg_cur_24h,

		(select servers.ip,round(avg(metr.conn), 1) as avg_cur_3d from servers
		left join {metrics} as metr on metr.serv = servers.ip
		where servers.{metrics} = 1 and
		metr.date <= datetime('now', 'localtime') and metr.date >= datetime('now', '-3 days', 'localtime')
		group by servers.ip ) as avg_cur_3d,

		(select servers.ip,max(metr.conn) as max_con_1h from servers
		left join {metrics} as metr on metr.serv = servers.ip
		where servers.{metrics} = 1 and
		metr.date <= datetime('now', 'localtime') and metr.date >= datetime('now', '-1 hours', 'localtime')
		group by servers.ip)   as max_con_1h,

		(select servers.ip,max(metr.conn) as max_con_24h from servers
		left join {metrics} as metr on metr.serv = servers.ip
		where servers.{metrics} = 1 and
		metr.date <= datetime('now', 'localtime') and metr.date >= datetime('now', '-24 hours', 'localtime')
		group by servers.ip) as max_con_24h,

		(select servers.ip,max(metr.conn) as max_con_3d from servers
		left join {metrics} as metr on metr.serv = servers.ip
		where servers.{metrics} = 1 and
		metr.date <= datetime('now', 'localtime') and metr.date >= datetime('now', '-3 days', 'localtime')
		group by servers.ip ) as max_con_3d

		where ip.ip=hostname.ip
		and ip.ip=avg_cur_1h.ip
		and ip.ip=avg_cur_24h.ip
		and ip.ip=avg_cur_3d.ip
		and ip.ip=max_con_1h.ip
		and ip.ip=max_con_24h.ip
		and ip.ip=max_con_3d.ip

		group by hostname.ip """.format(metrics=metrics_table, groups=groups)

	try:
		cursor.execute(sql)
	except Exception as e:
		out_error(e)
	else:
		return cursor.fetchall()
