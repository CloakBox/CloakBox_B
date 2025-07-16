import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from flask import request
import settings

class JWTManager:
    """ JWT 토큰 관리 클래스 """

    def __init__(self):
        self.secret_key = getattr(settings, 'JWT_SECRET_KEY', 'default_secret_key')
        self.algorithm = 'HS256'
        self.access_token_expire_minutes = getattr(settings, 'JWT_ACCESS_TOKEN_EXPIRE_MINUTES', 30)
        self.refresh_token_expire_minutes = getattr(settings, 'JWT_REFRESH_TOKEN_EXPIRE_MINUTES', 60 * 24 * 30)
        self._logger = None  # lazy loading
        self._blacklisted_tokens = set()  # TODO Redis 로 변경
    
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
            # 블랙리스트 확인
            if token in self._blacklisted_tokens:
                self.logger.warning("토큰 검증 실패: 블랙리스트된 토큰")
                return None
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

    def extract_user_info(self, token: str) -> Optional[Dict[str, Any]]:
        """토큰에서 사용자 정보 추출"""
        try:
            payload = self.verify_token(token)
            if not payload:
                self.logger.warning("사용자 정보 추출 실패: 유효하지 않은 토큰")
                return None
            
            # 토큰 타입 확인
            if payload.get('type') != 'access':
                self.logger.warning("사용자 정보 추출 실패: 액세스 토큰이 아님")
                return None
            
            user_info = {
                'email': payload.get('email'),
                'nickname': payload.get('nickname'),
                'user_id': payload.get('user_id')
            }
            
            if not user_info['email']:
                self.logger.warning("사용자 정보 추출 실패: 토큰에 이메일 정보 없음")
                return None
            
            self.logger.info(f"사용자 정보 추출 성공: {user_info['email']}")
            return user_info
            
        except Exception as e:
            self.logger.error(f"사용자 정보 추출 중 오류: {str(e)}")
            return None

    def validate_request_and_extract_user(self) -> Optional[Dict[str, Any]]:
        """Request에서 토큰을 검증하고 사용자 정보 추출"""
        try:
            # Authorization 헤더 확인
            auth_header = request.headers.get('Authorization')
            if not auth_header:
                self.logger.warning("Request 검증 실패: Authorization 헤더 없음")
                return None
            
            # Bearer 토큰 형식 확인
            if not auth_header.startswith('Bearer '):
                self.logger.warning("Request 검증 실패: 잘못된 토큰 형식")
                return None
            
            # 토큰 추출
            token = auth_header.split(' ')[1]
            
            # 토큰에서 사용자 정보 추출
            user_info = self.extract_user_info(token)
            if not user_info:
                self.logger.warning("Request 검증 실패: 사용자 정보 추출 실패")
                return None
            
            self.logger.info(f"Request 검증 성공: {user_info['email']}")
            return user_info
            
        except Exception as e:
            self.logger.error(f"Request 검증 중 오류: {str(e)}")
            return None

    def invalidate_token(self, token: str) -> bool:
        """토큰을 무효화 (블랙리스트에 추가)"""
        try:
            # 토큰 유효성 검증
            payload = self.verify_token(token)
            if not payload:
                self.logger.warning("토큰 무효화 실패: 유효하지 않은 토큰")
                return False
            
            # 블랙리스트에 추가
            self._blacklisted_tokens.add(token)
            self.logger.info(f"토큰 무효화 완료: {payload.get('email', 'unknown')}")
            return True
            
        except Exception as e:
            self.logger.error(f"토큰 무효화 중 오류: {str(e)}")
            return False

    def invalidate_request_token(self) -> bool:
        """Request에서 토큰을 추출하여 무효화"""
        try:
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                self.logger.warning("토큰 무효화 실패: Authorization 헤더 없음")
                return False
            
            token = auth_header.split(' ')[1]
            return self.invalidate_token(token)
            
        except Exception as e:
            self.logger.error(f"Request 토큰 무효화 중 오류: {str(e)}")
            return False

jwt_manager = JWTManager()