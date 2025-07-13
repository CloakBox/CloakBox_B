import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import settings

class JWTManager:
    """ JWT 토큰 관리 클래스 """

    def __init__(self):
        self.secret_key = getattr(settings, 'JWT_SECRET_KEY', 'default_secret_key')
        self.algorithm = 'HS256'
        self.access_token_expire_minutes = getattr(settings, 'JWT_ACCESS_TOKEN_EXPIRE_MINUTES', 30)
        self.refresh_token_expire_minutes = getattr(settings, 'JWT_REFRESH_TOKEN_EXPIRE_MINUTES', 60 * 24 * 30)
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """ 액세스 토큰 생성 """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({'exp': expire, 'type': 'access'})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """ 리프레시 토큰 생성 """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.refresh_token_expire_minutes)
        to_encode.update({'exp': expire, 'type': 'refresh'})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """ 토큰 검증 """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """ 토큰 디코딩 """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

jwt_manager = JWTManager()