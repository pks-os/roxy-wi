from typing import Union, Literal

from flask import request
from flask.views import MethodView
from flask_pydantic import validate
from flask_jwt_extended import jwt_required

import app.modules.roxywi.common as roxywi_common
import app.modules.db.service as service_sql
import app.modules.service.installation as service_mod
from app.middleware import get_user_params, check_services, page_for_admin, check_group
from app.modules.common.common_classes import SupportClass
from app.modules.roxywi.class_models import BaseResponse, ServiceInstall
from app.views.service.views import ServiceView


class InstallGetStatus(ServiceView):
    methods = ['GET']
    decorators = [jwt_required(), get_user_params(), check_services, page_for_admin(level=3), check_group()]

    def get(self, service: Literal['haproxy', 'nginx', 'apache', 'keepalived'], server_id: Union[int, str]):
        """
        This endpoint retrieves information about a specific service.
        ---
        tags:
          - Service Installation
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
                Process:
                  type: 'string'
                  description: 'Number of processes launched by the service'
                Status:
                  type: 'string'
                  description: 'Status of the service'
          default:
            description: Unexpected error
        """
        return super().get(service=service, server_id=server_id)


class InstallView(MethodView):
    methods = ['POST']
    decorators = [jwt_required(), get_user_params(), check_services, page_for_admin(level=3), check_group()]

    @validate(body=ServiceInstall)
    def post(self, service: Literal['haproxy', 'nginx', 'apache', 'keepalived'], server_id: Union[int, str, None], body: ServiceInstall):
        """
        Install a specific service.
        ---
        tags:
          - Service Installation
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
              type: 'object'
              properties:
                servers:
                  type: 'array'
                  items:
                    type: 'object'
                    properties:
                      id:
                        type: 'integer'
                      name:
                        type: 'string'
                services:
                  type: 'object'
                  description: 'Which service will be installed.'
                  properties:
                    haproxy:
                      type: 'object'
                      description: 'Status of HAProxy'
                      properties:
                        enabled:
                          type: 'integer'
                        docker:
                          type: 'integer'
                syn_flood:
                  type: 'integer'
                checker:
                  type: 'integer'
                metrics:
                  type: 'integer'
                auto_start:
                  type: 'integer'
          default:
            description: Unexpected error
        """
        try:
            if server_id is not None:
                server_id = SupportClass().return_server_ip_or_id(server_id)
        except Exception as e:
            return roxywi_common.handler_exceptions_for_json_data(e, '')
        try:
            output = service_mod.install_service(service, body)
        except Exception as e:
            return roxywi_common.handler_exceptions_for_json_data(e, f'Cannot install {service.title()}')

        if 'api' in request.url:
            try:
                service_sql.update_hapwi_server(server_id, body.checker, body.metrics, body.auto_start, service)
                if len(output['failures']) > 0 or len(output['dark']) > 0:
                    raise Exception(f'Cannot install {service.title()}. Check Apache error log')
            except Exception as e:
                return roxywi_common.handler_exceptions_for_json_data(e, f'Cannot update Tools settings for {service.title()}')
        else:
            return output
        return BaseResponse().model_dump(mode='json'), 201
