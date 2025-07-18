CREATE TABLE user_image (
	id BIGSERIAL PRIMARY KEY,
	uuid UUID NOT NULL,
	size BIGINT	NULL,
	path VARCHAR(255) NULL,
	name VARCHAR(255) NULL,
	extension VARCHAR(50) NULL
);

COMMENT ON TABLE user_image IS '사용자 이미지 테이블';
COMMENT ON COLUMN user_image.id IS '사용자 이미지 ID';
COMMENT ON COLUMN user_image.uuid IS '사용자 이미지 UUID';
COMMENT ON COLUMN user_image.size IS '사용자 이미지 사이즈';
COMMENT ON COLUMN user_image.path IS '사용자 이미지 경로';
COMMENT ON COLUMN user_image.name IS '사용자 이미지 이름';
COMMENT ON COLUMN user_image.extension IS '사용자 이미지 확장자';

CREATE TABLE user_setting (
	id BIGSERIAL PRIMARY KEY,
	dark_mode VARCHAR(1) NULL DEFAULT 'N',
	editor_mode	VARCHAR(50) NULL,
	lang_cd	VARCHAR(255) NULL DEFAULT 'ko'
);

COMMENT ON TABLE user_setting IS '사용자 설정 테이블';
COMMENT ON COLUMN user_setting.id IS '사용자 설정 ID';
COMMENT ON COLUMN user_setting.dark_mode IS '다크모드 여부';
COMMENT ON COLUMN user_setting.editor_mode IS '에디터 설정';
COMMENT ON COLUMN user_setting.lang_cd IS '언어 설정';

CREATE TABLE user_event_log (
	id	BIGSERIAL PRIMARY KEY,
	user_uuid UUID NOT NULL,
	event_type VARCHAR(255)	NOT NULL,
	event_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	event_at_unix BIGINT NULL
);

COMMENT ON TABLE user_event_log IS '사용자 이벤트 로그 테이블';
COMMENT ON COLUMN user_event_log.id IS '사용자 이벤트 로그 ID';
COMMENT ON COLUMN user_event_log.user_uuid IS '사용자 UUID';
COMMENT ON COLUMN user_event_log.event_type IS '이벤트 타입';
COMMENT ON COLUMN user_event_log.event_at IS '이벤트 일시';
COMMENT ON COLUMN user_event_log.event_at_unix IS '이벤트 일시 UNIX timestamp (ms)';

ALTER TABLE users ADD COLUMN user_setting_id BIGINT NULL;