from extensions import db
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import func
import time

class UserLoginLog(db.Model):
    __tablename__ = 'user_login_log'

    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(UUID(as_uuid=True), nullable=False)
    event_type = db.Column(db.String(20), default='LOGIN')
    event_at = db.Column(db.DateTime, default=func.current_timestamp(), nullable=False)
    event_at_unix = db.Column(db.BigInteger, default=func.extract('epoch', func.current_timestamp()), nullable=False)
    ip_id = db.Column(db.BigInteger, nullable=False)
    user_agent_id = db.Column(db.BigInteger, nullable=False)

    def __init__(self, user_id: UUID, event_type: str = 'LOGIN', ip_id: int = None, user_agent_id: int = None):
        self.user_id = user_id
        self.event_type = event_type
        self.ip_id = ip_id
        self.user_agent_id = user_agent_id

    def __repr__(self):
        return f"<UserLoginLog {self.id}>"