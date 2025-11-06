from flask_restx import Resource
from flask import request
from app.api.v1 import api, alerts_ns
from app.services.alert_service import AlertService
from app.utils.decorators import validate_auth_and_role
from models import Role


alert_service = AlertService()


@alerts_ns.route('/')
class AlertList(Resource):
    @alerts_ns.doc('list_alerts')
    def get(self):
        params = {
            'status': request.args.get('status', 'PENDING'),
        }
        data, status = alert_service.list_alerts(params)
        return data, status
