from sqlalchemy.orm import Session

from ..models import Notification


def notify(db: Session, user_id: int, kind: str, message: str, related_type=None, related_id=None):
    row = Notification(
        user_id=user_id, type=kind, message=message,
        related_type=related_type, related_id=related_id,
    )
    db.add(row)
    return row
