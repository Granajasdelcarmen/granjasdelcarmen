from flask_restx import Resource, fields
from flask import request
from app.api.v1 import api, alerts_ns
from app.services.alert_service import AlertService
from app.utils.decorators import validate_auth_and_role
from models import Role


alert_service = AlertService()

# API Models
decline_alert_model = api.model('DeclineAlert', {
    'reason': fields.String(required=True, description='Reason for declining the alert')
})

complete_alert_model = api.model('CompleteAlert', {
    'slaughtered_rabbit_ids': fields.List(fields.String(), required=False, description='List of rabbit IDs that were slaughtered (only for SLAUGHTER_REMINDER alerts)')
})


@alerts_ns.route('/')
class AlertList(Resource):
    @alerts_ns.doc('list_alerts')
    def get(self):
        params = {
            'status': request.args.get('status', 'PENDING'),
        }
        data, status = alert_service.list_alerts(params)
        return data, status


@alerts_ns.route('/<int:alert_id>/complete')
class CompleteAlert(Resource):
    @alerts_ns.doc('complete_alert')
    @alerts_ns.expect(complete_alert_model)
    def post(self, alert_id):
        """Mark an alert as completed. For SLAUGHTER_REMINDER alerts, requires slaughtered_rabbit_ids list."""
        user, error = validate_auth_and_role([Role.ADMIN, Role.USER, Role.TRABAJADOR])
        if error:
            return error[0], error[1]
        
        request_data = request.get_json() or {}
        slaughtered_rabbit_ids = request_data.get('slaughtered_rabbit_ids')
        
        data, status = alert_service.complete_alert(alert_id, slaughtered_rabbit_ids)
        return data, status


@alerts_ns.route('/<int:alert_id>/rabbits')
class AlertRabbits(Resource):
    @alerts_ns.doc('get_alert_rabbits')
    def get(self, alert_id):
        """Get list of rabbits associated with a SLAUGHTER_REMINDER alert"""
        user, error = validate_auth_and_role([Role.ADMIN, Role.USER, Role.TRABAJADOR])
        if error:
            return error[0], error[1]
        
        from app.utils.database import get_db_session
        from models import Alert, Animal, AnimalType
        from datetime import datetime
        import json
        
        with get_db_session() as db:
            alert = db.query(Alert).filter(Alert.id == alert_id).first()
            
            if not alert:
                from app.utils.response import not_found_response
                return not_found_response("Alert")
            
            if alert.name != 'SLAUGHTER_REMINDER' or alert.animal_type != AnimalType.RABBIT:
                from app.utils.response import error_response
                return error_response("This endpoint is only for SLAUGHTER_REMINDER alerts", 400)
            
            # Obtener IDs de conejos de la alerta
            rabbit_ids = []
            if hasattr(alert, 'rabbit_ids') and alert.rabbit_ids:
                try:
                    rabbit_ids = json.loads(alert.rabbit_ids)
                except (json.JSONDecodeError, TypeError):
                    pass
            
            # Si no hay rabbit_ids (alerta antigua), buscar conejos por la madre o por rango de edad
            if not rabbit_ids:
                from datetime import timedelta
                from app.services.rabbit_alert_service import RabbitAlertService
                
                rabbit_alert_service = RabbitAlertService()
                today = datetime.utcnow()
                min_birth_date = today - timedelta(days=rabbit_alert_service.SLAUGHTER_MAX_DAYS)
                max_birth_date = today - timedelta(days=rabbit_alert_service.SLAUGHTER_MIN_DAYS)
                
                # Buscar conejos no criadores en el rango de edad
                # NO filtrar por slaughtered, para incluir todos los conejos originales
                query = db.query(Animal).filter(
                    Animal.species == AnimalType.RABBIT,
                    Animal.is_breeder == False,
                    Animal.discarded == False,  # Solo excluir descartados
                    Animal.birth_date >= min_birth_date,
                    Animal.birth_date <= max_birth_date
                )
                
                # Si la alerta tiene animal_id (madre), filtrar por hijos de esa madre
                if alert.animal_id:
                    query = query.filter(Animal.mother_id == alert.animal_id)
                
                rabbits_to_slaughter = query.all()
                rabbit_ids = [r.id for r in rabbits_to_slaughter]
                
                # Si encontramos conejos y la alerta no tenía rabbit_ids, guardarlos
                if rabbit_ids:
                    # Verificar si la alerta realmente no tenía rabbit_ids antes
                    current_rabbit_ids = None
                    if hasattr(alert, 'rabbit_ids') and alert.rabbit_ids:
                        try:
                            current_rabbit_ids = json.loads(alert.rabbit_ids)
                        except (json.JSONDecodeError, TypeError):
                            pass
                    
                    # Solo guardar si realmente no tenía rabbit_ids
                    if not current_rabbit_ids:
                        alert.rabbit_ids = json.dumps(rabbit_ids)
                        db.commit()
            
            # Obtener información de los conejos
            # Buscar TODOS los conejos de la alerta, incluso los ya sacrificados
            rabbits = []
            if rabbit_ids:
                rabbits_query = db.query(Animal).filter(
                    Animal.id.in_(rabbit_ids),
                    Animal.species == AnimalType.RABBIT
                ).all()
                
                rabbits = [{
                    'id': r.id,
                    'name': r.name,
                    'birth_date': r.birth_date.isoformat() if r.birth_date else None,
                    'gender': r.gender.name if r.gender else None,
                    'slaughtered': getattr(r, 'slaughtered', False),
                    'in_freezer': getattr(r, 'in_freezer', False),
                } for r in rabbits_query]
            
            from app.utils.response import success_response
            return success_response(rabbits, "Rabbits retrieved successfully")


@alerts_ns.route('/<int:alert_id>/decline')
class DeclineAlert(Resource):
    @alerts_ns.doc('decline_alert')
    @alerts_ns.expect(decline_alert_model)
    def post(self, alert_id):
        """Decline an alert with a reason"""
        user, error = validate_auth_and_role([Role.ADMIN, Role.USER, Role.TRABAJADOR])
        if error:
            return error[0], error[1]
        
        data = request.get_json()
        reason = data.get('reason', '')
        data, status = alert_service.decline_alert(alert_id, reason)
        return data, status


@alerts_ns.route('/verify')
class VerifyAlerts(Resource):
    @alerts_ns.doc('verify_alerts')
    def post(self):
        """Verify and update alerts status (expired, completed automatically)"""
        user, error = validate_auth_and_role([Role.ADMIN, Role.USER, Role.TRABAJADOR])
        if error:
            return error[0], error[1]
        
        alert_service.verify_and_update_alerts()
        
        return {'message': 'Alerts verified and updated successfully'}, 200
