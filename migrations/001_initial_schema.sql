CREATE TABLE IF NOT EXISTS processed_videos (
    video_id VARCHAR(32) PRIMARY KEY,
    source_url TEXT NOT NULL,
    transcript TEXT NOT NULL,
    content_type VARCHAR(64) NOT NULL,
    summary TEXT NOT NULL,
    twi_text TEXT NOT NULL,
    audio_data BLOB,
    audio_content_type VARCHAR(64),
    hit_count INTEGER NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    last_accessed_at DATETIME
);

CREATE TABLE IF NOT EXISTS request_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    url TEXT NOT NULL,
    video_id VARCHAR(32),
    status VARCHAR(32) NOT NULL DEFAULT 'started',
    cache_hit BOOLEAN NOT NULL DEFAULT 0,
    error_message TEXT,
    created_at DATETIME NOT NULL,
    completed_at DATETIME
);

CREATE INDEX IF NOT EXISTS ix_request_logs_chat_id ON request_logs (chat_id);
CREATE INDEX IF NOT EXISTS ix_request_logs_video_id ON request_logs (video_id);
