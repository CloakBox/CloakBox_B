from pydantic import BaseModel, Field, field_validator
from typing import Optional
import re

class SendCertificationCodeDTO(BaseModel):
    email: str = Field(..., description="인증번호를 받을 이메일")

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('유효하지 않은 이메일 형식입니다.')
        return v.lower()
    
class VerifyCertificationCodeDTO(BaseModel):
    email: str = Field(..., description="인증번호를 받을 이메일")
    code: str = Field(..., min_length=1, max_length=20, description="인증번호")

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('유효하지 않은 이메일 형식입니다.')
        return v.lower()