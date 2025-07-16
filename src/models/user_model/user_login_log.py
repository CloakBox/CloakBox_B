from extensions import db
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import UUID
import time

class UserLoginLog(db.Model):
    __tablename__ = 'user_login_log'

    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.UUID, nullable=False)
    event_type = db.Column(db.String(20), default='LOGIN')
    event_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    event_at_unix = db.Column(db.BigInteger, default=int(time.time()))
    ip_id = db.Column(db.BigInteger, nullable=False)
    user_agent_id = db.Column(db.BigInteger, nullable=False)

    def __init__(self, user_id: UUID, event_type: str = 'LOGIN', ip_id: int = None, user_agent_id: int = None):
        self.user_id = user_id
        self.event_type = event_type
        self.event_at = datetime.now(timezone.utc)
        self.event_at_unix = int(time.time())
        self.ip_id = ip_id
        self.user_agent_id = user_agent_id

    def __repr__(self):
        return f"<UserLoginLog {self.id}>"