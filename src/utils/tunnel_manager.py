import threading
from typing import Dict, Optional
import atexit
import time
import signal
import sys
from sshtunnel import SSHTunnelForwarder
import sys
import settings

from .loging_manager import get_app_logger

class SSHTunnel:
    """SSH 터널링 클래스"""
    def __init__(self):
        self.tunnel: Optional[SSHTunnelForwarder] = None
        self.local_port: Optional[int] = None
        self._lock = threading.Lock()
        self._is_active = False
        self.logger = get_app_logger()
    
    def create_tunnel(self) -> bool:
        """SSH 터널링 생성"""
        with self._lock:
            if self._is_active:
                self.logger.info("SSH 터널이 이미 활성화되어 있습니다.")
                return True
                
            try:
                # SSH 터널 설정
                self.tunnel = SSHTunnelForwarder(
                    (settings.SSH_HOST, settings.SSH_PORT),
                    ssh_username=settings.SSH_USER,
                    ssh_password=settings.SSH_PASSWORD,
                    remote_bind_address=(settings.REMOTE_DB_HOST, settings.REMOTE_DB_PORT),
                    local_bind_address=('localhost', 0),
                    allow_agent=False,
                    set_keepalive=60.0
                )
                
                # 터널 시작
                self.tunnel.start()
                
                # 로컬 포트 가져오기
                self.local_port = self.tunnel.local_bind_port
                self._is_active = True
                
                self.logger.info(f"SSH 터널링 생성 완료: localhost:{self.local_port} -> {settings.SSH_HOST}:{settings.SSH_PORT} -> {settings.REMOTE_DB_HOST}:{settings.REMOTE_DB_PORT}")
                return True
                
            except Exception as e:
                self.logger.error(f"SSH 터널링 생성 실패: {str(e)}")
                self.close_tunnel()
                raise e

    def close_tunnel(self) -> None:
        """SSH 터널링 종료"""
        with self._lock:
            if self.tunnel and self._is_active:
                try:
                    self.tunnel.stop()
                    self.tunnel = None
                    self.local_port = None
                    self._is_active = False
                    self.logger.info("SSH 터널링 종료")
                except Exception as e:
                    self.logger.error(f"SSH 터널링 종료 중 오류: {str(e)}")
    
    def is_active(self) -> bool:
        """터널이 활성 상태인지 확인"""
        if not self._is_active or not self.tunnel:
            return False
        try:
            return bool(self.tunnel.is_active)
        except AttributeError:
            return self.tunnel is not None

    def get_local_port(self) -> Optional[int]:
        """로컬 포트 반환"""
        return self.local_port if self._is_active else None

class TunnelManager:
    def __init__(self):
        self.tunnels: Dict[str, SSHTunnel] = {}
        self.lock = threading.Lock()
        self.logger = get_app_logger()
    
    def get_or_create_tunnel(self, tunnel_key: str = "default") -> Optional[SSHTunnel]:
        """터널을 가져오거나 생성"""
        with self.lock:
            if tunnel_key not in self.tunnels:
                try:
                    tunnel = SSHTunnel()
                    if tunnel.create_tunnel():
                        self.tunnels[tunnel_key] = tunnel
                        self.logger.info(f"새로운 SSH 터널 생성: {tunnel_key} -> localhost:{tunnel.local_port}")
                    else:
                        return None
                except Exception as e:
                    self.logger.error(f"터널 생성 실패: {str(e)}")
                    return None
            
            return self.tunnels[tunnel_key]
    
    def close_tunnel(self, tunnel_key: str = "default") -> None:
        """특정 터널 종료"""
        with self.lock:
            if tunnel_key in self.tunnels:
                self.tunnels[tunnel_key].close_tunnel()
                del self.tunnels[tunnel_key]
                self.logger.info(f"터널 종료: {tunnel_key}")
    
    def close_all_tunnels(self) -> None:
        """모든 터널 종료"""
        with self.lock:
            for key, tunnel in self.tunnels.items():
                tunnel.close_tunnel()
            self.tunnels.clear()
            self.logger.info("모든 SSH 터널 종료")

    def run_standalone_tunnel(self):
        """독립 실행용 터널링"""
        def signal_handler(sig, frame):
            self.logger.info('SSH 터널링을 종료합니다...')
            self.close_all_tunnels()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        
        if not hasattr(settings, 'SSH_TUNNEL_ENABLED') or not settings.SSH_TUNNEL_ENABLED:
            self.logger.warning("SSH 터널링이 비활성화되어 있습니다.")
            return
        
        try:
            # TunnelManager를 사용하여 터널 생성
            tunnel = self.get_or_create_tunnel("standalone")
            if not tunnel:
                raise Exception("SSH 터널링 생성 실패")
            
            self.logger.info(f"SSH 터널링이 실행 중입니다. 로컬 포트: {tunnel.local_port}")
            self.logger.info("터널링을 종료하려면 Ctrl+C를 누르세요.")
            
            # 터널링을 계속 유지
            while True:
                time.sleep(1)
                    
        except KeyboardInterrupt:
            self.logger.info("SSH 터널링을 종료합니다.")
            self.close_all_tunnels()
        except Exception as e:
            self.logger.error(f"SSH 터널링 오류: {str(e)}")
            self.close_all_tunnels()

# 전역 터널 매니저
tunnel_manager = TunnelManager()

# 앱 종료 시 자동 정리 등록
atexit.register(tunnel_manager.close_all_tunnels)