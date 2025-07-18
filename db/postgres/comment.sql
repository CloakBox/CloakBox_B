-- 사용자 정보 테이블
COMMENT ON TABLE users IS '사용자 정보 테이블';
COMMENT ON COLUMN users.id IS '사용자UUID';
COMMENT ON COLUMN users.name IS '사용자명';
COMMENT ON COLUMN users.email IS '이메일';
COMMENT ON COLUMN users.role_id IS '권한';
COMMENT ON COLUMN users.nickname IS '닉네임';
COMMENT ON COLUMN users.bio IS '자기소개';
COMMENT ON COLUMN users.birth IS '생년월일';
COMMENT ON COLUMN users.gender IS '성별';
COMMENT ON COLUMN users.login_type IS '로그인 구분';
COMMENT ON COLUMN users.login_yn IS '로그인가능여부';
COMMENT ON COLUMN users.created_at_unix IS '생성일자 UNIX timestamp (ms)';
COMMENT ON COLUMN users.created_at IS '생성일자';
COMMENT ON COLUMN users.user_ip_id IS '로그인 IP';
COMMENT ON COLUMN users.user_agent_id IS '로그인 에이전트';
COMMENT ON COLUMN users.updated_at IS '업데이트 일자';
COMMENT ON COLUMN users.user_image_id IS '사용자 이미지 ID';
COMMENT ON COLUMN users.user_setting_id IS '사용자 설정 ID';

-- 사용자 로그인 로그 테이블
COMMENT ON TABLE user_login_log IS '사용자 로그인 로그 테이블';
COMMENT ON COLUMN user_login_log.id IS '사용자 로그인 로그 ID';
COMMENT ON COLUMN user_login_log.user_id IS '사용자 ID';
COMMENT ON COLUMN user_login_log.event_type IS '이벤트 타입';
COMMENT ON COLUMN user_login_log.event_at IS '이벤트 일시';
COMMENT ON COLUMN user_login_log.event_at_unix IS '이벤트 일시 UNIX timestamp (ms)';
COMMENT ON COLUMN user_login_log.ip_id IS 'IP ID';
COMMENT ON COLUMN user_login_log.user_agent_id IS '사용자 에이전트 ID';

-- 사용자 IP 테이블
COMMENT ON TABLE user_ip IS '사용자 IP 테이블';
COMMENT ON COLUMN user_ip.id IS '사용자 IP ID';
COMMENT ON COLUMN user_ip.ip_str IS '사용자 IP 주소';

-- 사용자 에이전트 테이블
COMMENT ON TABLE user_agent IS '사용자 에이전트 테이블';
COMMENT ON COLUMN user_agent.id IS '사용자 에이전트 ID';
COMMENT ON COLUMN user_agent.user_agent_str IS '사용자 에이전트 문자열';

-- 사용자 인증 테이블
COMMENT ON TABLE user_certification IS '사용자 인증 테이블';
COMMENT ON COLUMN user_certification.id IS '사용자 인증 ID';
COMMENT ON COLUMN user_certification.user_uuid IS '사용자 UUID';
COMMENT ON COLUMN user_certification.code IS '인증 코드';
COMMENT ON COLUMN user_certification.recipient IS '인증 수신자';
COMMENT ON COLUMN user_certification.use_yn IS '인증 사용 여부';
COMMENT ON COLUMN user_certification.created_at IS '인증 생성 일시';
COMMENT ON COLUMN user_certification.created_at_unix IS '인증 생성 일시 UNIX timestamp (ms)';
COMMENT ON COLUMN user_certification.expires_at IS '인증 만료 일시';
COMMENT ON COLUMN user_certification.expires_at_unix IS '인증 만료 일시 UNIX timestamp (ms)';

-- 사용자 이미지 테이블
COMMENT ON TABLE user_image IS '사용자 이미지 테이블';
COMMENT ON COLUMN user_image.id IS '사용자 이미지 ID';
COMMENT ON COLUMN user_image.uuid IS '사용자 이미지 UUID';
COMMENT ON COLUMN user_image.size IS '사용자 이미지 사이즈';
COMMENT ON COLUMN user_image.path IS '사용자 이미지 경로';
COMMENT ON COLUMN user_image.name IS '사용자 이미지 이름';
COMMENT ON COLUMN user_image.extension IS '사용자 이미지 확장자';

-- 사용자 설정 테이블
COMMENT ON TABLE user_setting IS '사용자 설정 테이블';
COMMENT ON COLUMN user_setting.id IS '사용자 설정 ID';
COMMENT ON COLUMN user_setting.dark_mode IS '다크모드 여부';
COMMENT ON COLUMN user_setting.editor_mode IS '에디터 설정';
COMMENT ON COLUMN user_setting.lang_cd IS '언어 설정';

-- 사용자 이벤트 로그 테이블
COMMENT ON TABLE user_event_log IS '사용자 이벤트 로그 테이블';
COMMENT ON COLUMN user_event_log.id IS '사용자 이벤트 로그 ID';
COMMENT ON COLUMN user_event_log.user_uuid IS '사용자 UUID';
COMMENT ON COLUMN user_event_log.event_type IS '이벤트 타입';
COMMENT ON COLUMN user_event_log.event_at IS '이벤트 일시';
COMMENT ON COLUMN user_event_log.event_at_unix IS '이벤트 일시 UNIX timestamp (ms)';