from extensions import db
from sqlalchemy import Column, Integer, String

class UserIp(db.Model):
    __tablename__ = 'user_ip'

    id = db.Column(db.BigInteger, primary_key=True)
    ip_str = db.Column(db.String(255), nullable=False)

    def __init__(self, ip_str: str):
        self.ip_str = ip_str

    def __repr__(self):
        return f"<UserIp {self.ip_str}>"