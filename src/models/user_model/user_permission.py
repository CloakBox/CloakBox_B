from extensions import db
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import func, text
import time

class UserPermission(db.Model):
    """ 사용자 권한 모델 """
    
    __tablename__ = "user_permission"
    
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False, primary_key=True)
    codebase_id = db.Column(UUID(as_uuid=True), db.ForeignKey('codebase.id'), nullable=False, primary_key=True)
    permission_type = db.Column(db.String(20), nullable=False)
    
    def __init__(self, user_id: UUID, codebase_id: UUID, permission_type: str):
        self.user_id = user_id
        self.codebase_id = codebase_id
        self.permission_type = permission_type