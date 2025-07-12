from extensions import db
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import UUID
import uuid

class User(db.Model):
    """ 사용자 모델 """
    
    __tablename__ = "users"
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    
    def __init__(self, name: str, email: str, password: str):
        self.name = name
        self.email = email
        self.password = password
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def __repr__(self):
        return f"<User {self.name}>"