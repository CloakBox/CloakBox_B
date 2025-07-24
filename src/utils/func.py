
def get_user_ip(request, db):
    
    from models.user_model.user_ip import UserIp
    
    # 사용자 IP와 User-Agent 정보 추출
    user_ip_str = request.remote_addr

    # IP 정보 저장 또는 조회
    user_ip_record = UserIp.query.filter_by(ip_str=user_ip_str).first()
    if not user_ip_record:
        user_ip_record = UserIp(ip_str=user_ip_str)
        db.session.add(user_ip_record)
        db.session.flush()
    
    return user_ip_record.id

def get_user_agent(request, db):
    
    from models.user_model.user_agent import UserAgent
    
    user_agent_str = request.headers.get('User-Agent', '')
    
    # User-Agent 정보 저장 또는 조회
    user_agent_record = UserAgent.query.filter_by(user_agent_str=user_agent_str).first()
    if not user_agent_record:
        user_agent_record = UserAgent(user_agent_str=user_agent_str)
        db.session.add(user_agent_record)
        db.session.flush()
    
    return user_agent_record.id