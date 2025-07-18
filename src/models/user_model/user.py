from extensions import db
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import func, text
import time

class User(db.Model):
    """ 사용자 모델 """
    
    __tablename__ = "users"
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=text('gen_random_uuid()'))
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    role_id = db.Column(db.BigInteger, nullable=True)
    nickname = db.Column(db.String(50), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    birth = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(10), nullable=True)
    login_type = db.Column(db.String(20), nullable=True)
    login_yn = db.Column(db.Boolean, nullable=True, default=True)
    created_at_unix = db.Column(db.BigInteger, nullable=True)
    created_at = db.Column(db.DateTime, default=func.current_timestamp(), nullable=True)
    user_ip_id = db.Column(db.BigInteger, nullable=True)
    user_agent_id = db.Column(db.BigInteger, nullable=True)
    updated_at = db.Column(db.DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=True)
    user_image_id = db.Column(db.BigInteger, nullable=True)
    user_setting_id = db.Column(db.BigInteger, nullable=True)
    
    def __init__(self, name: str, email: str, nickname: str, gender: str, bio: str, user_setting_id: int, **kwargs):
        self.name = name
        self.email = email
        self.nickname = nickname
        self.gender = gender
        self.bio = bio
        self.user_setting_id = user_setting_id
        self.create_at_unix = int(time.time())
        
        # 추가 필드들 설정
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def to_dict(self) -> dict:
        """사용자 정보를 딕셔너리로 변환"""
        return {
            'id': str(self.id),
            'name': self.name,
            'email': self.email,
            'nickname': self.nickname,
            'bio': self.bio,
            'birth': self.birth.isoformat() if self.birth else None,
            'gender': self.gender,
            'login_type': self.login_type,
            'login_yn': self.login_yn,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f"<User {self.name}>"