import os
import smtplib
from .loging_manager import get_app_logger
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
        self.logger = get_app_logger()
    
    def send_email(self, to_email: str, subject: str, body: str,
                    body_type: str = 'plain',
                    attachments=None):
        """이메일 전송"""
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
        
        try:
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
        except Exception as e:
            self.logger.error(f"이메일 전송 실패: {str(e)}")
            return False