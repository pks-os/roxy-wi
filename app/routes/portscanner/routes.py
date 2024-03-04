from flask import render_template, request, g
from flask_login import login_required

from app.routes.portscanner import bp
from app.middleware import get_user_params
import app.modules.db.server as server_sql
import app.modules.db.portscanner as ps_sql
import app.modules.common.common as common
import app.modules.server.server as server_mod
import app.modules.roxywi.common as roxywi_common
import app.modules.tools.common as tools_common


@bp.before_request
@login_required
def before_request():
    """ Protect all the admin endpoints. """
    pass


@bp.route('')
@get_user_params(virt=1)
def portscanner():
    port_scanner_settings = ps_sql.select_port_scanner_settings(g.user_params['group_id'])

    if not port_scanner_settings:
        port_scanner_settings = ''
        count_ports = ''
    else:
        count_ports = list()
        for s in g.user_params['servers']:
            count_ports_from_sql = ps_sql.select_count_opened_ports(s[2])
            i = (s[2], count_ports_from_sql)
            count_ports.append(i)

    kwargs = {
        'servers': g.user_params['servers'],
        'port_scanner_settings': port_scanner_settings,
        'count_ports': count_ports,
        'port_scanner': tools_common.is_tool_active('roxy-wi-portscanner'),
        'lang': g.user_params['lang'],
        'user_subscription': roxywi_common.return_user_subscription()
    }

    return render_template('portscanner.html', **kwargs)


@bp.route('/history/<server_ip>')
@get_user_params()
def portscanner_history(server_ip):
    kwargs = {
        'h2': 1,
        'lang': g.user_params['lang'],
        'history': ps_sql.select_port_scanner_history(server_ip),
        'user_subscription': roxywi_common.return_user_subscription()
    }

    return render_template('include/port_scan_history.html', **kwargs)


@bp.post('/settings')
def change_settings_portscanner():
    server_id = common.checkAjaxInput(request.form.get('server_id'))
    enabled = common.checkAjaxInput(request.form.get('enabled'))
    notify = common.checkAjaxInput(request.form.get('notify'))
    history = common.checkAjaxInput(request.form.get('history'))
    user_group_id = [server[3] for server in server_sql.select_servers(id=server_id)]

    try:
        if ps_sql.insert_port_scanner_settings(server_id, user_group_id[0], enabled, notify, history):
            return 'ok'
        else:
            if ps_sql.update_port_scanner_settings(server_id, user_group_id[0], enabled, notify, history):
                return 'ok'
    except Exception as e:
        return f'error: Cannot save settings: {e}'
    else:
        return 'ok'


@bp.route('/scan/<int:server_id>', defaults={'server_ip': None})
@bp.route('/scan/<server_ip>', defaults={'server_id': None})
def scan_port(server_id, server_ip):
    if server_ip:
        ip = server_ip
    else:
        server = server_sql.select_servers(id=server_id)
        ip = ''

        for s in server:
            ip = s[2]

    cmd = f"sudo nmap -sS {ip} |grep -E '^[[:digit:]]'|sed 's/  */ /g'"
    cmd1 = f"sudo nmap -sS {ip} |head -5|tail -2"

    stdout, stderr = server_mod.subprocess_execute(cmd)
    stdout1, stderr1 = server_mod.subprocess_execute(cmd1)

    if stderr != '':
        return f'error: {stderr}'
    else:
        lang = roxywi_common.get_user_lang_for_flask()
        return render_template('ajax/scan_ports.html', ports=stdout, info=stdout1, lang=lang)
