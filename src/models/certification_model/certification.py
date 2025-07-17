from extensions import db
from datetime import datetime, timedelta
from typing import Optional, Union
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy import func, text
import uuid
import settings

class UserCertification(db.Model):
    """ 사용자 인증 모델 """
    
    __tablename__ = "user_certification"
    
    id = db.Column(db.BigInteger, primary_key=True)
    user_uuid = db.Column(db.UUID, nullable=True)
    code = db.Column(db.String(10), nullable=False)
    recipient = db.Column(db.String(255), nullable=False)
    use_yn = db.Column(db.Boolean, default=False, nullable=True)
    created_at = db.Column(TIMESTAMP(timezone=True), default=func.now(), nullable=True)
    created_at_unix = db.Column(db.BigInteger, default=text('EXTRACT(epoch FROM now())'), nullable=True)
    expires_at = db.Column(TIMESTAMP(timezone=True), nullable=False)
    expires_at_unix = db.Column(db.BigInteger, default=text('EXTRACT(epoch FROM now())'), nullable=False)
    
    def __init__(self, recipient: str, code: str, user_uuid: Optional[Union[str, uuid.UUID]] = None):
        self.recipient = recipient.lower()
        self.code = code
        
        if user_uuid:
            if isinstance(user_uuid, str):
                self.user_uuid = user_uuid
            elif isinstance(user_uuid, uuid.UUID):
                self.user_uuid = str(user_uuid)
            else:
                self.user_uuid = None
        else:
            self.user_uuid = None
            
        current_time = datetime.now()
        self.created_at = current_time
        self.created_at_unix = int(current_time.timestamp())
        expire_minutes = getattr(settings, 'CERTIFICATION_CODE_EXPIRE_MINUTES', 5)
        self.expires_at = current_time + timedelta(minutes=expire_minutes)
        self.expires_at_unix = int(self.expires_at.timestamp())
    
    def is_expired(self) -> bool:
        """ 인증코드 만료 여부 확인 """
        current_time_unix = int(datetime.now().timestamp())
        return current_time_unix > self.expires_at_unix
    
    def is_valid(self) -> bool:
        """ 인증코드 유효성 확인 - use_yn이 False이고 만료되지 않았으면 유효 """
        return self.use_yn == False and not self.is_expired()
    
    def mark_as_used(self):
        """ 인증코드 사용 처리 """
        self.use_yn = True
    
    def __repr__(self):
        return f"<UserCertification {self.recipient}:{self.code}>"