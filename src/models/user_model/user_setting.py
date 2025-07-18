from extensions import db

class UserSetting(db.Model):
    """ 사용자 설정 모델 """
    
    __tablename__ = "user_setting"
    
    id = db.Column(db.BigInteger, primary_key=True)
    dark_mode = db.Column(db.String(1), nullable=True, default='N')
    editor_mode = db.Column(db.String(50), nullable=True)
    lang_cd = db.Column(db.String(255), nullable=True, default='ko')

    def __init__(self, dark_mode: str, editor_mode: str, lang_cd: str):
        self.dark_mode = dark_mode
        self.editor_mode = editor_mode
        self.lang_cd = lang_cd
    
    def __repr__(self):
        return f"<UserSetting {self.id}>"