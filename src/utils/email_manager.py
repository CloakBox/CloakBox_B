import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import settings

class EmailManager:
    def __init__(self):
        self.user = getattr(settings, 'EMAIL_USER', '')
        self.app_password = getattr(settings, 'EMAIL_APP_PASSWORD', '')
        self.smtp_server = getattr(settings, 'EMAIL_SMTP_SERVER', '')
        self.smtp_port = getattr(settings, 'EMAIL_SMTP_PORT', 0)
        self.use_ssl = getattr(settings, 'EMAIL_USE_SSL', True)
        self._logger = None  # lazy loading
    
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
    
    def send_email(self, to_email: str, subject: str, body: str,
                    body_type: str = 'plain',
                    attachments=None):
        """이메일 전송"""
        try:
            # 설정 검증
            if not self.user or not self.app_password or not self.smtp_server:
                self.logger.error("이메일 설정이 누락되었습니다.")
                return False
            
            msg = MIMEMultipart()
            msg['Subject'] = subject
            msg['From'] = self.user
            msg['To'] = to_email

            body_part = MIMEText(body, body_type)
            msg.attach(body_part)

            if attachments:
                for file_path in attachments:
                    try:
                        with open(file_path, 'rb') as f:
                            part = MIMEApplication(f.read(), Name=os.path.basename(file_path))
                            part['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
                            msg.attach(part)
                    except Exception as e:
                        self.logger.error(f"이메일 첨부파일 추가 실패: {str(e)}")
                        continue
            
            self.logger.info(f"이메일 전송 시도: {to_email}, SMTP: {self.smtp_server}:{self.smtp_port}")
            
            if self.use_ssl:
                with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as smtp:
                    smtp.login(self.user, self.app_password)
                    smtp.sendmail(self.user, to_email, msg.as_string())
            else:
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as smtp:
                    smtp.starttls()
                    smtp.login(self.user, self.app_password)
                    smtp.sendmail(self.user, to_email, msg.as_string())
        
            self.logger.info(f"이메일 전송 완료: {to_email}")
            return True
        except smtplib.SMTPAuthenticationError as e:
            self.logger.error(f"이메일 인증 실패: {str(e)}")
            return False
        except smtplib.SMTPException as e:
            self.logger.error(f"SMTP 오류: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"이메일 전송 실패: {str(e)}")
            return False