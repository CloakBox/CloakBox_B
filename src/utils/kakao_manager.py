import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import settings

class KaKaoManager:
    """카카오 API 관리 클래스"""
    
    def __init__(self):
        self.rest_api_key = getattr(settings, 'KAKAO_REST_API_KEY')
        self.redirect_uri = getattr(settings, 'KAKAO_REDIRECT_URI')
        self.client_secret = getattr(settings, 'KAKAO_CLIENT_SECRET')
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

    # 카카오 인증 URL 생성 ( account_email,profile_nickname,friends,talk_message )
    def get_auth_url(self, scope: str = "account_email,profile_nickname", prompt: str = "consent,login") -> str:
        """ 카카오 인증 URL 생성 """
        if not self.rest_api_key:
            raise ValueError("KAKAO_REST_API_KEY 설정이 되지 않았습니다.")
        
        auth_url = (
            f"https://kauth.kakao.com/oauth/authorize?"
            f"client_id={self.rest_api_key}&"
            f"redirect_uri={self.redirect_uri}&"
            f"response_type=code&"
            f"scope={scope}&"
            f"prompt={prompt}"
        )
        return auth_url
    
    def exchange_code_for_token(self, code: str) -> Dict:
        """ 인증 코드를 액세스 토큰으로 교환 """
        if not self.rest_api_key or not self.client_secret:
            raise ValueError("KAKAO_REST_API_KEY 또는 KAKAO_CLIENT_SECRET 설정이 되지 않았습니다.")
        
        token_url = "https://kauth.kakao.com/oauth/token"
        data = {
            "grant_type": "authorization_code",
            "client_id": self.rest_api_key,
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
        if not self.rest_api_key or not self.client_secret:
            raise ValueError("KAKAO_REST_API_KEY 또는 KAKAO_CLIENT_SECRET 설정이 되지 않았습니다.")
        
        refresh_url = "https://kauth.kakao.com/oauth/token"
        data = {
            "grant_type": "refresh_token",
            "client_id": self.rest_api_key,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token
        }
        
        response = requests.post(refresh_url, data=data)
        
        if response.status_code != 200:
            error_data = response.json()
            error_msg = error_data.get('error_description', error_data.get('error', '알 수 없는 오류'))
            
        return response.json()
    
    def get_token_info(self, access_token: str) -> Dict:
        """ 엑세스 토큰 정보 조회 """
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get("https://kapi.kakao.com/v1/user/access_token_info", headers=headers)
        
        if response.status_code != 200:
            error_data = response.json()
            error_msg = error_data.get('error_description', error_data.get('error', '알 수 없는 오류'))
            raise Exception(f"토큰 정보 조회 실패: {error_msg}")
    
        return response.json()
    
    def get_user_scope(self, access_token: str) -> Dict:
        """ 사용자 동의 항목 조회 """
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get("https://kapi.kakao.com/v2/user/scopes", headers=headers)
        
        if response.status_code != 200:
            error_data = response.json()
            error_msg = error_data.get('error_description', error_data.get('error', '알 수 없는 오류'))
            raise Exception(f"동의 항목 조회 실패: {error_msg}")
        
        return response.json()
    
    def get_user_info(self, access_token: str) -> Dict:
        """ 카카오 사용자 기본 정보 조회 """
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get("https://kapi.kakao.com/v2/user/me", headers=headers)
        
        if response.status_code != 200:
            error_data = response.json()
            error_msg = error_data.get('error_description', error_data.get('error', '알 수 없는 오류'))
            raise Exception(f"사용자 정보 조회 실패: {error_msg}")
        
        return response.json()
    
    def get_friend_info(self, access_token: str) -> Dict:
        """ 친구 목록 조회 """
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get("https://kapi.kakao.com/v1/api/talk/friends", headers=headers)
        
        if response.status_code != 200:
            error_data = response.json()
            error_msg = error_data.get('error_description', error_data.get('error', '알 수 없는 오류'))
            raise Exception(f"친구 목록 조회 실패: {error_msg}")
        
        return response.json()
    
    def send_message_to_self(self, access_token: str, message: str, link_url: str = None) -> bool:
        """ 나에게 메시지 전송 """
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        template = {
            "object_type": "text",
            "text": message,
            "link": {
                "web_url": link_url or "https://kakao.com",
                "mobile_web_url": link_url or "https://kakao.com"
            },
            "button_title": "확인"
        }
        
        data = {"template_object": json.dumps(template)}
        
        response = requests.post(
            "https://kapi.kakao.com/v2/api/talk/memo/default/send",
            headers=headers,
            data=data
        )
        
        if response.status_code != 200:
            self.logger.error(f"카카오 메시지 전송 실패: {response.status_code} - {response.text}")
            return False
        
        return True

    def send_message_to_friend(self, access_token: str, friend_uuid: str, message: str, link_url: str = None) -> bool:
        """ 친구에게 메시지 전송 """
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        template = {
            "object_type": "text",
            "text": message,
            "link": {
                "web_url": link_url or "https://kakao.com",
                "mobile_web_url": link_url or "https://kakao.com"
            },
            "button_title": "확인"
        }
        
        data = {
            "template_object": json.dumps(template),
            "receiver_uuids": [friend_uuid]
        }
        
        response = requests.post(
            "https://kapi.kakao.com/v2/api/talk/memo/default/send",
            headers=headers,
            data=data
        )
        
        if response.status_code != 200:
            self.logger.error(f"친구에게 메시지 전송 실패: {response.status_code} - {response.text}")
            return False
        
        return True
    
    def send_alert_message(self, access_token: str, status: str, message: str, link_url: str = None) -> Tuple[bool, str]:
        """ 알림 메시지 전송 """
        try:
            alert_message = f"메시지"
            
            if self.send_message_to_self(access_token, alert_message, link_url):
                return True, "나에게 메시지 전송 성공"
        
            friend_info = self.get_friend_info(access_token)
            friends = friend_info.get('elements', [])
            
            if not friends:
                return False, "친구 목록이 없습니다."
            
            friend = friends[0]
            friend_uuid = friend.get('uuid')
            friend_name = friend.get('profile_nickname', '친구')
            
            if self.send_message_to_friend(access_token, friend_uuid, alert_message, link_url):
                return True, f"{friend_name}에게 메시지 전송 성공"
            else:
                return False, f"{friend_name}에게 메시지 전송 실패"
        except Exception as e:
            self.logger.error(f"알림 메시지 전송 실패: {str(e)}")
            return False, f"알림 메시지 전송 실패: {str(e)}"
    
    def validate_token(self, access_token: str) -> bool:
        """ 토큰 유효성 검사 """
        try:
            self.get_token_info(access_token)
            return True
        except Exception as e:
            self.logger.error(f"토큰 유효성 검사 실패: {str(e)}")
            return False
        
    def check_required_scope(self, access_token: str) -> Dict[str, bool]:
        """ 필요한 권한 확인 """
        try:
            scopes_data = self.get_user_scope(access_token)
            scopes = scopes_data.get('scopes', [])
            
            required_scopes = ["friends", "talk_message"]
            scopes_status = {}
            
            for scope in required_scopes:
                scopes_status[scope] = any(s.get('id') == scope for s in scopes)
            
            return scopes_status
        except Exception as e:
            self.logger.error(f"필요한 권한 확인 실패: {str(e)}")
            return {scope: False for scope in required_scopes}
    
    def create_test_message(self) -> str:
        """ 테스트 메시지 생성 """
        return "테스트 메시지입니다."
    
    def get_debug_info(self, access_token: str = None) -> Dict:
        """ 디버그 정보 조회 """
        debug_info = {
            "api_keys": {
                "rest_api_key": self.rest_api_key[:10] + "..." if self.rest_api_key else "설정되지 않음",
                "client_secret": self.client_secret[:10] + "..." if self.client_secret else "설정되지 않음",
                "redirect_uri": self.redirect_uri[:10] + "..." if self.redirect_uri else "설정되지 않음"
            },
            "token_info": {
                "has_token": bool(access_token),
                "is_valid": False
            }
        }
        
        if access_token:
            try:
                token_info = self.get_token_info(access_token)
                debug_info["token_info"]["is_valid"] = True
                debug_info["token_info"]["expires_at"] = token_info.get("expires_in")
                debug_info["token_info"]["app_id"] = token_info.get("app_id")
                
                # 스코프 정보 추가
                scopes_data = self.get_user_scope(access_token)
                scopes = []
                for scope in scopes_data.get("scopes", []):
                    scopes.append({
                        "id": scope.get("id"),
                        "display_name": scope.get("display_name"),
                        "using": scope.get("using", False)
                    })
                debug_info["token_info"]["scopes"] = scopes
                
            except Exception as e:
                debug_info["token_info"]["error"] = str(e)
        
        return debug_info