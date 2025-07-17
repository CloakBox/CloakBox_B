import requests
from datetime import datetime
from typing import Dict
import settings

class GoogleManager:
    """ 구글 API 관리 클래스 """

    def __init__(self):
        self.client_id = getattr(settings, 'GOOGLE_CLIENT_ID')
        self.client_secret = getattr(settings, 'GOOGLE_CLIENT_SECRET')
        self.redirect_uri = getattr(settings, 'GOOGLE_REDIRECT_URI')
        self._logger = None

    @property
    def logger(self):
        """로거 lazy loading"""
        if self._logger is None:
            try:
                from extensions import app_logger
                self._logger = app_logger
            except ImportError:
                # extensions가 아직 초기화되지 않은 경우 기본 로거 사용
                import logging
                logger = logging.getLogger('email_manager')
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
    
    def get_auth_url(self, scope: str = "email profile", prompt: str = "consent select_account"):
        """ 구글 인증 URL 생성 """
        if not self.client_id:
            raise ValueError("GOOGLE_CLIENT_ID 설정이 되지 않았습니다.")
        
        auth_url = (
            f"https://accounts.google.com/o/oauth2/v2/auth?"
            f"client_id={self.client_id}&"
            f"redirect_uri={self.redirect_uri}&"
            f"response_type=code&"
            f"scope={scope}&"
            f"prompt={prompt}&"
            f"access_type=offline"
        )
        return auth_url
    
    def exchange_code_for_token(self, code: str) -> Dict:
        """ 인증 코드를 액세스 토큰으로 교환 """
        if not self.client_id or not self.client_secret:
            raise ValueError("GOOGLE_CLIENT_ID 또는 GOOGLE_CLIENT_SECRET 설정이 되지 않았습니다.")

        token_url = "https://oauth2.googleapis.com/token"
        data = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "code": code
        }

        response = requests.post(token_url, data=data)
        
        if response.status_code != 200:
            error_data = response.json()
            error_msg = error_data.get('error_description', error_data.get('error', '알 수 없는 오류'))
            raise ValueError(f"토큰 교환 실패: {error_msg}")
        
        return response.json()
    
    def refresh_token(self, refresh_token: str) -> Dict:
        """ 리프레시 토큰으로 액세스 토큰 갱신 """
        if not self.client_id or not self.client_secret:
            raise ValueError("GOOGLE_CLIENT_ID 또는 GOOGLE_CLIENT_SECRET 설정이 되지 않았습니다.")

        refresh_url = "https://oauth2.googleapis.com/token"
        data = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token
        }

        response = requests.post(refresh_url, data=data)

        if response.status_code != 200:
            error_data = response.json()
            error_msg = error_data.get('error_description', error_data.get('error', '알 수 없는 오류'))
            raise ValueError(f"토큰 갱신 실패: {error_msg}")
        
        return response.json()
    
    def get_token_info(self, access_token: str) -> Dict:
        """ 액세스 토큰 정보 조회 """
        token_info_url = "https://www.googleapis.com/token_info?access_token={access_token}"
        response = requests.get(token_info_url)

        if response.status_code != 200:
            error_data = response.json()
            error_msg = error_data.get('error_description', error_data.get('error', '알 수 없는 오류'))
            raise ValueError(f"토큰 정보 조회 실패: {error_msg}")
        
        return response.json()
    
    def get_user_info(self, access_token: str) -> Dict:
        """ 구글 사용자 기본  정보 조회 """
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get("https://www.googleapis.com/oauth2/v2/userinfo", headers=headers)

        if response.status_code != 200:
            error_data = response.json()
            error_msg = error_data.get('error_description', error_data.get('error', '알 수 없는 오류'))
            raise ValueError(f"사용자 정보 조회 실패: {error_msg}")
        
        return response.json()
    
    def validate_token(self, access_token: str) -> bool:
        """ 액세스 토큰 유효성 검사 """
        try:
            self.get_token_info(access_token)
            return True
        except ValueError:
            return False
        
    def get_debug_info(self, access_token: str = None) -> Dict:
        """디버그 정보 조회"""
        debug_info = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "timestamp": datetime.now().isoformat()
        }
        
        if access_token:
            try:
                token_info = self.get_token_info(access_token)
                user_info = self.get_user_info(access_token)
                debug_info.update({
                    "token_info": token_info,
                    "user_info": user_info,
                    "token_valid": True
                })
            except Exception as e:
                debug_info.update({
                    "token_valid": False,
                    "error": str(e)
                })
        
        return debug_info