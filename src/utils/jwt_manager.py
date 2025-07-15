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
        self._logger = None  # lazy loading
    
    @property
    def logger(self):
        """로거 lazy loading"""
        if self._logger is None:
            try:
                from extensions import app_logger
                self._logger = app_logger
            except ImportError:
                import logging
                logger = logging.getLogger('jwt_manager')
                if not logger.handlers:
                    handler = logging.StreamHandler()
                    formatter = logging.Formatter(
                        '[%(asctime)s] %(levelname)s: %(module)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S'
                    )
                    handler.setFormatter(formatter)
                    logger.addHandler(handler)
                    logger.setLevel(logging.INFO)
                self._logger = logger
        return self._logger
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """ 액세스 토큰 생성 """
        try:
            to_encode = data.copy()
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
            to_encode.update({'exp': expire, 'type': 'access'})
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            self.logger.info(f"액세스 토큰 생성 완료: {data.get('user_id', 'unknown')}")
            return encoded_jwt
        except Exception as e:
            self.logger.error(f"액세스 토큰 생성 실패: {str(e)}")
            raise e
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """ 리프레시 토큰 생성 """
        try:
            to_encode = data.copy()
            expire = datetime.utcnow() + timedelta(minutes=self.refresh_token_expire_minutes)
            to_encode.update({'exp': expire, 'type': 'refresh'})
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            self.logger.info(f"리프레시 토큰 생성 완료: {data.get('user_id', 'unknown')}")
            return encoded_jwt
        except Exception as e:
            self.logger.error(f"리프레시 토큰 생성 실패: {str(e)}")
            raise e
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """ 토큰 검증 """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            self.logger.info(f"토큰 검증 성공: {payload.get('user_id', 'unknown')}")
            return payload
        except jwt.ExpiredSignatureError:
            self.logger.warning("토큰 만료됨")
            return None
        except jwt.InvalidTokenError as e:
            self.logger.warning(f"유효하지 않은 토큰: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"토큰 검증 중 오류: {str(e)}")
            return None
    
    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """ 토큰 디코딩 """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            self.logger.warning("토큰 만료됨")
            return None
        except jwt.InvalidTokenError as e:
            self.logger.warning(f"유효하지 않은 토큰: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"토큰 디코딩 중 오류: {str(e)}")
            return None

jwt_manager = JWTManager()