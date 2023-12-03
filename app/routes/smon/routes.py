import json
from pytz import timezone
from flask import render_template, request, jsonify, g
from flask_login import login_required
from datetime import datetime

from app.routes.smon import bp
from middleware import get_user_params
import app.modules.db.sql as sql
import app.modules.common.common as common
import app.modules.roxywi.auth as roxywi_auth
import app.modules.roxywi.common as roxywi_common
import app.modules.tools.smon as smon_mod


@bp.route('/dashboard')
@login_required
@get_user_params()
def smon():
    roxywi_common.check_user_group_for_flask()

    user_params = g.user_params
    user_group = roxywi_common.get_user_group(id=1)
    smon = sql.smon_list(user_group)
    smon_status, stderr = smon_mod.return_smon_status()
    user_subscription = roxywi_common.return_user_subscription()

    return render_template(
        'smon/dashboard.html', autorefresh=1, role=user_params['role'], user=user_params['user'], group=user_group,
        lang=user_params['lang'], smon_status=smon_status, smon_error=stderr, user_services=user_params['user_services'],
        user_status=user_subscription['user_status'], smon=smon, user_plan=user_subscription['user_plan'], token=user_params['token']
    )


@bp.route('/dashboard/<dashboard_id>/<check_id>')
@login_required
@get_user_params()
def smon_dashboard(dashboard_id, check_id):
    user_params = g.user_params
    check_id = int(check_id)
    roxywi_common.check_user_group_for_flask()
    user_subscription = roxywi_common.return_user_subscription()
    smon_name = sql.get_smon_service_name_by_id(dashboard_id)
    check_interval = sql.get_setting('smon_check_interval')
    smon = sql.select_one_smon(dashboard_id, check_id)
    present = datetime.now(timezone('UTC'))
    present = present.strftime('%b %d %H:%M:%S %Y %Z')
    present = datetime.strptime(present, '%b %d %H:%M:%S %Y %Z')
    cert_day_diff = 'N/A'
    uptime = smon_mod.check_uptime(dashboard_id)

    try:
        avg_res_time = round(sql.get_avg_resp_time(dashboard_id, check_id), 2)
    except Exception:
        avg_res_time = 0
    try:
        last_resp_time = round(sql.get_last_smon_res_time_by_check(dashboard_id, check_id), 2)
    except Exception:
        last_resp_time = 0

    for s in smon:
        if s.smon_id.ssl_expire_date is not None:
            ssl_expire_date = datetime.strptime(s.smon_id.ssl_expire_date, '%Y-%m-%d %H:%M:%S')
            cert_day_diff = (ssl_expire_date - present).days

    return render_template(
        'include/smon/smon_history.html', autorefresh=1, role=user_params['role'], user=user_params['user'], smon=smon,
        lang=user_params['lang'], user_status=user_subscription['user_status'], check_interval=check_interval,
        user_plan=user_subscription['user_plan'], token=user_params['token'], uptime=uptime, avg_res_time=avg_res_time,
        user_services=user_params['user_services'], smon_name=smon_name, cert_day_diff=cert_day_diff, check_id=check_id,
        dashboard_id=dashboard_id, last_resp_time=last_resp_time
    )


@bp.route('/status-page', methods=['GET', 'POST', 'DELETE', 'PUT'])
@login_required
@get_user_params()
def status_page():
    if request.method == 'GET':
        user_params = g.user_params
        user_group = roxywi_common.get_user_group(id=1)
        smon_list = sql.smon_list(user_group)
        pages = sql.select_status_pages(user_group)
        smon_status, stderr = smon_mod.return_smon_status()
        user_subscription = roxywi_common.return_user_subscription()

        return render_template(
            'smon/manage_status_page.html', role=user_params['role'], user=user_params['user'],
            lang=user_params['lang'], pages=pages, smon_status=smon_status,
            user_status=user_subscription['user_status'], user_plan=user_subscription['user_plan'], smon_error=stderr,
            token=user_params['token'], user_services=user_params['user_services'], smon=smon_list,
        )
    elif request.method == 'POST':
        name = common.checkAjaxInput(request.form.get('name'))
        slug = common.checkAjaxInput(request.form.get('slug'))
        desc = common.checkAjaxInput(request.form.get('desc'))
        checks = json.loads(request.form.get('checks'))

        if not len(checks['checks']):
            return 'error: Please check Checks for Status page'

        try:
            return smon_mod.create_status_page(name, slug, desc, checks['checks'])
        except Exception as e:
            return f'{e}'
    elif request.method == 'PUT':
        page_id = int(request.form.get('page_id'))
        name = common.checkAjaxInput(request.form.get('name'))
        slug = common.checkAjaxInput(request.form.get('slug'))
        desc = common.checkAjaxInput(request.form.get('desc'))
        checks = json.loads(request.form.get('checks'))

        if not len(checks['checks']):
            return 'error: Please check Checks for Status page'

        try:
            return smon_mod.edit_status_page(page_id, name, slug, desc, checks['checks'])
        except Exception as e:
            return f'{e}'
    elif request.method == 'DELETE':
        page_id = int(request.form.get('page_id'))
        try:
            sql.delete_status_page(page_id)
        except Exception as e:
            return f'{e}'
        else:
            return 'ok'


@bp.route('/status/checks/<int:page_id>')
@login_required
def get_checks(page_id):
    returned_check = []
    try:
        checks = sql.select_status_page_checks(page_id)
    except Exception as e:
        return f'error: Cannot get checks: {e}'

    for check in checks:
        returned_check.append(str(check.check_id))

    return jsonify(returned_check)


@bp.route('/status/<slug>')
def show_smon_status_page(slug):
    slug = common.checkAjaxInput(slug)

    return smon_mod.show_status_page(slug)


@bp.route('/status/avg/<int:page_id>')
def smon_history_statuses_avg(page_id):
    return smon_mod.avg_status_page_status(page_id)


@bp.route('/history')
@login_required
@get_user_params()
def smon_history():
    roxywi_common.check_user_group_for_flask()

    user_group = roxywi_common.get_user_group(id=1)
    smon_status, stderr = smon_mod.return_smon_status()
    smon = sql.alerts_history('SMON', user_group)
    user_subscription = roxywi_common.return_user_subscription()
    user_params = g.user_params

    return render_template(
        'smon/history.html', autorefresh=0, role=user_params['role'], user=user_params['user'], smon=smon, lang=user_params['lang'],
        user_status=user_subscription['user_status'], user_plan=user_subscription['user_plan'], token=user_params['token'],
        smon_status=smon_status, smon_error=stderr, user_services=user_params['user_services']
    )


@bp.route('/history/host/<server_ip>')
@login_required
@get_user_params()
def smon_host_history(server_ip):
    roxywi_common.check_user_group_for_flask()

    needed_host = common.is_ip_or_dns(server_ip)
    user_group = roxywi_common.get_user_group(id=1)
    smon_status, stderr = smon_mod.return_smon_status()
    smon = sql.alerts_history('SMON', user_group, host=needed_host)
    user_subscription = roxywi_common.return_user_subscription()
    user_params = g.user_params

    return render_template(
        'smon/history.html', autorefresh=0, role=user_params['role'], user=user_params['user'], smon=smon,
        lang=user_params['lang'], user_status=user_subscription['user_status'], user_plan=user_subscription['user_plan'],
        token=user_params['token'], smon_status=smon_status, smon_error=stderr, user_services=user_params['user_services']
    )


@bp.route('/history/metric/<int:dashboard_id>')
@login_required
def smon_history_metric(dashboard_id):
    return jsonify(smon_mod.history_metrics(dashboard_id))


@bp.route('/history/statuses/<int:dashboard_id>')
def smon_history_statuses(dashboard_id):
    return smon_mod.history_statuses(dashboard_id)


@bp.route('/history/cur_status/<int:dashboard_id>/<int:check_id>')
@login_required
def smon_history_cur_status(dashboard_id, check_id):
    return smon_mod.history_cur_status(dashboard_id, check_id)


@bp.route('/admin')
@login_required
@get_user_params()
def smon_admin():
    user_group = roxywi_common.get_user_group(id=1)
    smon_status, stderr = smon_mod.return_smon_status()
    telegrams = sql.get_user_telegram_by_group(user_group)
    slacks = sql.get_user_slack_by_group(user_group)
    pds = sql.get_user_pd_by_group(user_group)
    smon = sql.select_smon(user_group)
    smon_ping = sql.select_smon_ping(user_group)
    smon_tcp = sql.select_smon_tcp(user_group)
    smon_http = sql.select_smon_http(user_group)
    smon_dns = sql.select_smon_dns(user_group)
    roxywi_auth.page_for_admin(level=3)
    user_subscription = roxywi_common.return_user_subscription()
    user_params = g.user_params

    return render_template(
        'smon/add.html', autorefresh=0, role=user_params['role'], user=user_params['user'], smon=smon, lang=user_params['lang'],
        user_status=user_subscription['user_status'], user_plan=user_subscription['user_plan'], token=user_params['token'],
        smon_status=smon_status, smon_error=stderr, user_services=user_params['user_services'], telegrams=telegrams,
        slacks=slacks, pds=pds, smon_ping=smon_ping, smon_tcp=smon_tcp, smon_http=smon_http, smon_dns=smon_dns
    )


@bp.post('/add')
@login_required
def smon_add():
    user_group = roxywi_common.get_user_group(id=1)
    name = common.checkAjaxInput(request.form.get('newsmonname'))
    hostname = common.checkAjaxInput(request.form.get('newsmon'))
    port = common.checkAjaxInput(request.form.get('newsmonport'))
    enable = common.checkAjaxInput(request.form.get('newsmonenable'))
    url = common.checkAjaxInput(request.form.get('newsmonurl'))
    body = common.checkAjaxInput(request.form.get('newsmonbody'))
    group = common.checkAjaxInput(request.form.get('newsmongroup'))
    desc = common.checkAjaxInput(request.form.get('newsmondescription'))
    telegram = common.checkAjaxInput(request.form.get('newsmontelegram'))
    slack = common.checkAjaxInput(request.form.get('newsmonslack'))
    pd = common.checkAjaxInput(request.form.get('newsmonpd'))
    check_type = common.checkAjaxInput(request.form.get('newsmonchecktype'))
    resolver = common.checkAjaxInput(request.form.get('newsmonresserver'))
    record_type = common.checkAjaxInput(request.form.get('newsmondns_record_type'))
    packet_size = common.checkAjaxInput(request.form.get('newsmonpacket_size'))
    http_method = common.checkAjaxInput(request.form.get('newsmon_http_method'))
    lang = roxywi_common.get_user_lang_for_flask()

    try:
        last_id = smon_mod.create_smon(
            name, hostname, port, enable, url, body, group, desc, telegram, slack, pd, packet_size, check_type,
            resolver, record_type, user_group, http_method
        )
    except Exception as e:
        return str(e), 200
    else:
        if last_id:
            smon = sql.select_smon_by_id(last_id)
            pds = sql.get_user_pd_by_group(user_group)
            slacks = sql.get_user_slack_by_group(user_group)
            telegrams = sql.get_user_telegram_by_group(user_group)
            smon_service = sql.select_smon_check_by_id(last_id, check_type)

            return render_template(
                'ajax/smon/show_new_smon.html', smon=smon, telegrams=telegrams, slacks=slacks, pds=pds, lang=lang,
                check_type=check_type, smon_service=smon_service
            )


@bp.post('/update/<smon_id>')
@login_required
def smon_update(smon_id):
    roxywi_common.check_user_group_for_flask()
    name = common.checkAjaxInput(request.form.get('updateSmonName'))
    ip = common.checkAjaxInput(request.form.get('updateSmonIp'))
    port = common.checkAjaxInput(request.form.get('updateSmonPort'))
    en = common.checkAjaxInput(request.form.get('updateSmonEn'))
    url = common.checkAjaxInput(request.form.get('updateSmonUrl'))
    body = common.checkAjaxInput(request.form.get('updateSmonBody'))
    telegram = common.checkAjaxInput(request.form.get('updateSmonTelegram'))
    slack = common.checkAjaxInput(request.form.get('updateSmonSlack'))
    pd = common.checkAjaxInput(request.form.get('updateSmonPD'))
    group = common.checkAjaxInput(request.form.get('updateSmonGroup'))
    desc = common.checkAjaxInput(request.form.get('updateSmonDesc'))
    check_type = common.checkAjaxInput(request.form.get('check_type'))
    resolver = common.checkAjaxInput(request.form.get('updateSmonResServer'))
    record_type = common.checkAjaxInput(request.form.get('updateSmonRecordType'))
    packet_size = common.checkAjaxInput(request.form.get('updateSmonPacket_size'))
    http_method = common.checkAjaxInput(request.form.get('updateSmon_http_method'))

    if roxywi_common.check_user_group_for_flask():
        try:
            status = smon_mod.update_smon(
                smon_id, name, ip, port, en, url, body, telegram, slack, pd, group, desc, check_type,
                resolver, record_type, packet_size, http_method
            )
        except Exception as e:
            return f'{e}', 200
        else:
            return status


@bp.route('/delete/<smon_id>')
@login_required
def smon_delete(smon_id):
    user_group = roxywi_common.get_user_group(id=1)

    if roxywi_common.check_user_group_for_flask():
        try:
            status = smon_mod.delete_smon(smon_id, user_group)
        except Exception as e:
            return f'{e}', 200
        else:
            return status


@bp.post('/refresh')
@login_required
def smon_show():
    sort = common.checkAjaxInput(request.form.get('sort'))
    return smon_mod.show_smon(sort)
