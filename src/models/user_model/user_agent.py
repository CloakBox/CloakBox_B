from extensions import db
from sqlalchemy import Column, Integer, String

class UserAgent(db.Model):
    __tablename__ = 'user_agent'

    id = db.Column(db.BigInteger, primary_key=True)
    user_agent_str = db.Column(db.String(255), nullable=False)

    def __init__(self, user_agent_str: str):
        self.user_agent_str = user_agent_str