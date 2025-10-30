from typing import List, Optional
from sqlalchemy.orm import Session
from app.repositories.base import BaseRepository
from models import Alert, AlertStatus


class AlertRepository(BaseRepository[Alert]):
    def __init__(self, model: Alert, db_session: Session):
        super().__init__(model, db_session)

    def list_pending_by_urgency(
        self,
        *,
        status: AlertStatus = AlertStatus.PENDING,
        limit: Optional[int] = 100,
    ) -> List[Alert]:
        query = self.query().filter(Alert.status == status)
        query = query.order_by(Alert.max_date.asc())
        if limit:
            query = query.limit(limit)
        return query.all()
