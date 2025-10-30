from typing import Dict, Any
from app.repositories.alert_repository import AlertRepository
from app.utils.database import get_db_session
from app.utils.response import success_response, error_response
from models import Alert, AlertStatus


class AlertService:
    def list_alerts(self, params: Dict[str, Any]) -> tuple:
        try:
            with get_db_session() as db:
                repo = AlertRepository(Alert, db)
                status = params.get('status', 'PENDING')
                alerts = repo.list_pending_by_urgency(status=AlertStatus(status))
                return success_response([self._serialize(a) for a in alerts])
        except Exception as e:
            return error_response(str(e), 500)

    def _serialize(self, a: Alert) -> Dict[str, Any]:
        return {
            'id': a.id,
            'name': a.name,
            'description': a.description,
            'init_date': a.init_date.isoformat() if a.init_date else None,
            'max_date': a.max_date.isoformat() if a.max_date else None,
            'status': a.status.name if a.status else None,
            'priority': a.priority.name if a.priority else None,
            'animal_type': a.animal_type.name if a.animal_type else None,
            'animal_id': a.animal_id,
            'corral_id': a.corral_id,
            'event_id': a.event_id,
            'created_at': a.created_at.isoformat() if a.created_at else None,
            'updated_at': a.updated_at.isoformat() if a.updated_at else None,
        }
