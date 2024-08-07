from typing import Union, Literal

from flask.views import MethodView
from flask_pydantic import validate
from flask import jsonify, g
from flask_jwt_extended import jwt_required

import app.modules.db.sql as sql
import app.modules.db.server as server_sql
import app.modules.db.service as service_sql
import app.modules.roxywi.common as roxywi_common
import app.modules.config.config as config_mod
import app.modules.config.common as config_common
import app.modules.server.server as server_mod
import app.modules.service.action as service_action
import app.modules.service.common as service_common
from app.middleware import get_user_params, page_for_admin, check_group, check_services
from app.modules.roxywi.exception import RoxywiResourceNotFound
from app.modules.roxywi.class_models import BaseResponse, ErrorResponse, DataResponse, DataStrResponse, ConfigFileNameQuery, ConfigRequest
from app.modules.common.common_classes import SupportClass


class ServiceView(MethodView):
    methods = ['GET']
    decorators = [jwt_required(), get_user_params(), check_services, page_for_admin(level=4), check_group()]

    def get(self, service: Literal['haproxy', 'nginx', 'apache', 'keepalived'], server_id: Union[int, str]):
        """
        This endpoint retrieves information about a specific service.
        ---
        tags:
          - Service
        parameters:
          - in: path
            name: service
            type: 'string'
            required: true
            description: The type of service (haproxy, nginx, apache, keepalived)
          - in: path
            name: server_id
            type: 'integer'
            required: true
            description: The ID or IP of the server
        responses:
          200:
            description: Successful operation
            schema:
              type: 'object'
              properties:
                CurrConns:
                  type: 'string'
                  description: 'Current connections to HAProxy (only for HAProxy service)'
                Maxconn:
                  type: 'string'
                  description: 'Maximum connections to HAProxy (only for HAProxy service)'
                MaxconnReached:
                  type: 'string'
                  description: 'Max connections reached (only for HAProxy service)'
                Memmax_MB:
                  type: 'string'
                  description: 'Maximum memory in MB (only for HAProxy service)'
                PoolAlloc_MB:
                  type: 'string'
                  description: 'Memory pool allocated in MB (only for HAProxy service)'
                PoolUsed_MB:
                  type: 'string'
                  description: 'Memory pool used in MB (only for HAProxy service)'
                Uptime:
                  type: 'string'
                  description: 'Time the service has been active'
                Version:
                  type: 'string'
                  description: 'Version of the service'
          default:
            description: Unexpected error
        """
        try:
            server_id = SupportClass().return_server_ip_or_id(server_id)
        except Exception as e:
            return roxywi_common.handler_exceptions_for_json_data(e, '')

        try:
            server = server_sql.get_server_with_group(server_id, g.user_params['group_id'])
        except Exception as e:
            return roxywi_common.handler_exceptions_for_json_data(e, 'Cannot find a server')

        if service == 'haproxy':
            cmd = 'echo "show info" |nc %s %s -w 1|grep -e "Ver\|CurrConns\|Maxco\|MB\|Uptime:"' % (
            server.ip, sql.get_setting('haproxy_sock_port'))
            out = server_mod.subprocess_execute(cmd)
            data = self.return_dict_from_out(out[0])
            if len(data) == 0:
                data = ErrorResponse(error='Cannot get information').model_dump(mode='json')
        elif service == 'nginx':
            is_dockerized = service_sql.select_service_setting(server_id, service, 'dockerized')
            if is_dockerized == '1':
                cmd = ("docker exec -it {container_name} /usr/sbin/nginx -v 2>&1|awk '{print $3}' && systemctl status nginx "
                       "|grep -e 'Active'|awk '{print $2, $9$10$11$12$13}' && ps ax |grep nginx:|grep -v grep |wc -l")
            else:
                cmd = ("/usr/sbin/nginx -v 2>&1|awk '{print $3}' && systemctl status nginx |grep -e 'Active'"
                       "|awk '{print $2, $9$10$11$12$13}' && ps ax |grep nginx:|grep -v grep |wc -l")
            try:
                out = server_mod.ssh_command(server.ip, cmd)
                out1 = out.split()
                data = {"Version": out1[0].split('/')[1], "Uptime": out1[2], "Process": out1[3]}
            except Exception as e:
                data = ErrorResponse(error=str(e)).model_dump(mode='json')
        elif service == 'apache':
            apache_stats_user = sql.get_setting('apache_stats_user')
            apache_stats_password = sql.get_setting('apache_stats_password')
            apache_stats_port = sql.get_setting('apache_stats_port')
            apache_stats_page = sql.get_setting('apache_stats_page')
            cmd = "curl -s -u %s:%s http://%s:%s/%s?auto |grep 'ServerVersion\|Processes\|ServerUptime:'" % \
                  (apache_stats_user, apache_stats_password, server.ip, apache_stats_port, apache_stats_page)
            servers_with_status = list()
            try:
                out = server_mod.subprocess_execute(cmd)
                if out != '':
                    for k in out:
                        servers_with_status.append(k)
                data = {
                    "Version": servers_with_status[0][0].split('/')[1],
                    "Uptime": servers_with_status[0][1].split(':')[1].strip(),
                    "Process": servers_with_status[0][2].split(' ')[1]
                }
            except Exception as e:
                data = ErrorResponse(error=str(e)).model_dump(mode='json')
        elif service == 'keepalived':
            cmd = "sudo /usr/sbin/keepalived -v 2>&1|head -1|awk '{print $2}'"
            try:
                version = server_mod.ssh_command(server.ip, cmd)
            except Exception as e:
                return roxywi_common.handler_exceptions_for_json_data(e, 'Cannot get version')
            if version == '/usr/sbin/keepalived:\r\n':
                return ErrorResponse(error='Cannot get keepalived').model_dump(mode='json')
            data = {'Version': version}
        return jsonify(data)

    @staticmethod
    def return_dict_from_out(out):
        data = {}
        for k in out:
            if "Ncat:" not in k:
                k = k.split(':')
                data[k[0]] = k[1].strip()
            else:
                data = {"error": "Cannot connect to HAProxy"}

        return data


class ServiceActionView(MethodView):
    methods = ['GET']
    decorators = [jwt_required(), get_user_params(), page_for_admin(level=3), check_group()]

    @staticmethod
    def get(service: str, server_id: Union[int, str], action: str):
        """
        This endpoint performs a specified action on a certain service on a specific server.
        ---
        tags:
          - Service
        parameters:
          - in: path
            name: service
            type: 'integer'
            required: true
            description: The type of service (haproxy, nginx, apache, keepalived, waf_haproxy, waf_nginx)
          - in: path
            name: server_id
            type: 'integer'
            required: true
            description: The ID or IP of the server
          - in: path
            name: action
            type: 'string'
            required: true
            description: The action to be performed on the service (start, stop, reload, restart)
        responses:
          200:
            description: Successful operation
          default:
            description: Unexpected error
        """
        if service not in ('haproxy', 'nginx', 'apache', 'keepalived', 'waf_haproxy', 'waf_nginx'):
            return roxywi_common.handler_exceptions_for_json_data(RoxywiResourceNotFound(), 'Cannot find a server')

        try:
            server_id = SupportClass().return_server_ip_or_id(server_id)
        except Exception as e:
            return roxywi_common.handler_exceptions_for_json_data(e, 'Cannot find a server')

        try:
            server = server_sql.get_server_with_group(server_id, g.user_params['group_id'])
        except Exception as e:
            return roxywi_common.handler_exceptions_for_json_data(e, 'Cannot find a server')

        try:
            service_action.common_action(server.ip, action, service)
            return BaseResponse().model_dump(mode='json')
        except Exception as e:
            return roxywi_common.handler_exceptions_for_json_data(e, f'Cannot do {action}')


class ServiceBackendView(MethodView):
    methods = ['GET', 'POST']
    decorators = [jwt_required(), get_user_params(), check_services, page_for_admin(level=4), check_group()]

    @staticmethod
    def get(service: str, server_id: Union[int, str]):
        """
        This endpoint retrieves information about service backends.
        ---
        tags:
          - Service
        parameters:
          - in: path
            name: service
            type: 'integer'
            required: true
            description: The type of service (haproxy, nginx, apache, keepalived)
          - in: path
            name: server_id
            type: 'integer'
            required: true
            description: The ID or IP of the server
        responses:
          200:
            description: Successful operation
            schema:
              type: 'array'
              items:
                ppoperties:
                  type: 'string'
                  description: 'List of backends (only for HAProxy and Keepalived services)'
          default:
            description: Unexpected error
        """
        try:
            server_ip = SupportClass(False).return_server_ip_or_id(server_id)
        except Exception as e:
            return roxywi_common.handler_exceptions_for_json_data(e, '')

        try:
            backends = service_common.overview_backends(server_ip, service)
            return DataResponse(data=backends).model_dump(mode='json')
        except Exception as e:
            return roxywi_common.handler_exceptions_for_json_data(e, 'Backends not found')


class ServiceConfigView(MethodView):
    methods = ['GET', 'POST']
    decorators = [jwt_required(), get_user_params(), check_services, page_for_admin(level=3), check_group()]

    @validate(query=ConfigFileNameQuery)
    def get(self, service: str, server_id: Union[int, str], query: ConfigFileNameQuery):
        """
        This endpoint retrieves the configuration file for the specified service on a certain server.
        ---
        tags:
          - Service config
        parameters:
          - in: path
            name: service
            type: 'integer'
            required: true
            description: The type of service (haproxy, nginx, apache, keepalived)
          - in: path
            name: server_id
            type: 'integer'
            required: true
            description: The ID or IP of the server
          - in: query
            name: file_name
            type: 'string'
            required: false
            description: The full path to the configuration file (used only for nginx and apache, replace "/" with 92)
          - in: query
            name: version
            type: 'string'
            required: false
            description: The version of the configuration file
        responses:
          200:
            description: 'Successful operation, returns the required configuration file'
          default:
            description: Unexpected error
        """
        if service in ('nginx', 'apache') and (query.file_name is None and query.version is None):
            return ErrorResponse(error=f'There is must be "file_name" as query parameter for {service.title()}')
        if query.file_name:
            query.file_name = query.file_name.replace('/', '92')

        try:
            server_ip = SupportClass(False).return_server_ip_or_id(server_id)
        except Exception as e:
            return roxywi_common.handler_exceptions_for_json_data(e, '')

        if query.version:
            configs_dir = config_common.get_config_dir(service)
            if '..' in configs_dir:
                return ErrorResponse(error='nice try').model_dump(mode='json')
            cfg = configs_dir + query.version
        else:
            cfg = config_common.generate_config_path(service, server_ip)
            try:
                config_mod.get_config(server_ip, cfg, service=service, config_file_name=query.file_name)
            except Exception as e:
                return ErrorResponse(error=str(e)).model_dump(mode='json')

        try:
            with open(cfg, 'r') as file:
                conf = file.readlines()
        except Exception as e:
            return roxywi_common.handler_exceptions_for_json_data(e, 'Cannot get config')

        return DataResponse(data=conf).model_dump(mode='json')

    @validate(body=ConfigRequest)
    def post(self, service: str, server_id: Union[int, str], body: ConfigRequest):
        """
        Update service configuration
        ---
        tags:
          - Service config
        parameters:
          - name: service
            in: path
            type: string
            required: true
            description: The service name, one of [haproxy, nginx, apache, keepalived].
          - name: server_id
            in: path
            type: string
            required: true
            description: Server Identifier - either ID or IP.
          - name: body
            in: body
            schema:
              type: object
              properties:
                action:
                  type: string
                  description: The action to be performed.
                  required: true
                config:
                  type: string
                  description: The configuration to be saved.
                  required: true
                file_name:
                  type: string
                  description: Path to the configuration file. Only for NGINX and Apache services.
                config_local_path:
                  type: string
                  description: Local path for the configuration, if updated from it. It could be used for uploading a version of config file.
              required:
                - action
        responses:
          200:
            description: Post request received successful
            schema:
              type: object
              properties:
                status:
                  type: string
                data:
                  type: string
                  description: Configuration check result
          default:
            description: Unexpected error
        """
        if service in ('nginx', 'apache') and (body.file_name is None):
            return ErrorResponse(error=f'There is must be "file_name" as json parameter for {service.title()}')
        try:
            server_ip = SupportClass(False).return_server_ip_or_id(server_id)
        except Exception as e:
            return roxywi_common.handler_exceptions_for_json_data(e, '')

        try:
            cfg = config_mod.return_cfg(service, server_ip, body.file_name)
        except Exception as e:
            return roxywi_common.handler_exceptions_for_json_data(e, 'Cannot get config')

        try:
            with open(cfg, "a") as conf:
                conf.write(body.config)
        except IOError as e:
            return roxywi_common.handler_exceptions_for_json_data(e, 'Cannot write config')

        try:
            if service == 'keepalived':
                stderr = config_mod.upload_and_restart(server_ip, cfg, body.action, service, oldcfg=body.config_local_path)
            else:
                stderr = config_mod.master_slave_upload_and_restart(server_ip, cfg, body.action, service, oldcfg=body.config_local_path,
                                                                    config_file_name=body.file_name)
        except Exception as e:
            return f'error: {e}', 200

        if body.action != 'test':
            config_mod.diff_config(body.config_local_path, cfg)


        return DataStrResponse(data=stderr).model_dump(mode='json'), 201


class ServiceConfigVersionsView(MethodView):
    methods = ['GET', 'POST']
    decorators = [jwt_required(), get_user_params(), check_services, page_for_admin(level=4), check_group()]

    def get(self, service, server_id: Union[int, str]):
        """
        This endpoint returns a list of configuration file versions for a specified service on a specific server.
        ---
        tags:
          - Service config
        parameters:
          - in: path
            name: service
            type: 'integer'
            required: true
            description: The type of service (haproxy, nginx, apache, keepalived)
          - in: path
            name: server_id
            type: 'integer'
            required: true
            description: The ID or IP of the server
        responses:
          200:
            description: 'Successful operation, returns list of configuration file versions'
          default:
            description: Unexpected error
        """
        try:
            server_ip = SupportClass(False).return_server_ip_or_id(server_id)
        except Exception as e:
            return roxywi_common.handler_exceptions_for_json_data(e ,'')

        config_dir = config_common.get_config_dir(service)
        file_format = config_common.get_file_format(service)
        files = roxywi_common.get_files(config_dir, file_format, server_ip)
        return DataResponse(data=files).model_dump(mode='json')
