from flask import Blueprint, request, jsonify
from extensions import db
import settings
from pydantic import ValidationError

from models.user_model.user import User
from models.user_model.user_register_dto import UserRegisterDTO
from service.user_logic import user_service

user_bp = Blueprint("user", __name__, url_prefix=f'/{settings.API_PREFIX}')

@user_bp.route('/user/register', methods=['POST'], endpoint='user_register')
def user_register():
    try:
        if not request.json:
            return jsonify({
                "status": "error",
                "message": "요청 데이터가 없습니다."
            }), 400
        
        # DTO를 사용한 입력 검증
        try:
            user_data = UserRegisterDTO(**request.json)
        except ValidationError as e:
            return jsonify({
                "status": "error",
                "message": "입력 데이터 검증 실패",
                "errors": e.errors()
            }), 400
        
        # 기존 사용자 확인
        existing_user = User.query.filter_by(email=user_data.email).first()
        if existing_user:
            return jsonify({
                "status": "error",
                "message": "이미 존재하는 이메일입니다."
            }), 400
        
        # 비밀번호 암호화
        hashed_password = user_service.hash_password(user_data.password)
        
        # 새 사용자 생성
        new_user = User(
            name=user_data.name,
            email=user_data.email,
            password=hashed_password
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "회원가입이 완료되었습니다.",
            "user": {
                "id": str(new_user.id),
                "name": new_user.name,
                "email": new_user.email,
                "created_at": new_user.created_at.isoformat()
            }
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": f"회원가입 중 오류가 발생했습니다: {str(e)}"
        }), 500

@user_bp.route('/user/login', methods=['POST'], endpoint='user_login')
def user_login():
    try:
        if not request.json:
            return jsonify({
                "status": "error",
                "message": "요청 데이터가 없습니다."
            }), 400
        
        email = request.json.get("email")
        password = request.json.get("password")
        
        if not email or not password:
            return jsonify({
                "status": "error",
                "message": "이메일과 비밀번호를 입력해주세요."
            }), 400
        
        # 사용자 조회
        user = User.query.filter_by(email=email.lower()).first()
        if not user:
            return jsonify({
                "status": "error",
                "message": "사용자를 찾을 수 없습니다."
            }), 404
        
        # 비밀번호 검증
        if not user_service.check_password_hash(password, user.password):
            return jsonify({
                "status": "error",
                "message": "비밀번호가 올바르지 않습니다."
            }), 401
        
        return jsonify({
            "status": "success",
            "message": "로그인이 완료되었습니다.",
            "user": {
                "id": str(user.id),
                "name": user.name,
                "email": user.email
            }
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"로그인 중 오류가 발생했습니다: {str(e)}"
        }), 500