"""Tests for the database repository layer."""

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.db.models import Base, ProcessedVideo, RequestLog
from app.db.repository import DatabaseRepository


def make_repository(tmp_path):
    """Create a repository backed by an isolated SQLite database."""
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )
    return DatabaseRepository(session_factory)


def test_upsert_and_get_processed_video(tmp_path):
    """Should cache processed video output and increment cache hit count."""
    repository = make_repository(tmp_path)

    repository.upsert_processed_video(
        video_id="dQw4w9WgXcQ",
        source_url="https://youtu.be/dQw4w9WgXcQ",
        transcript="Transcript",
        content_type="music",
        summary="Summary",
        twi_text="Twi summary",
        audio_data=b"mp3-bytes",
        audio_content_type="audio/mpeg",
    )

    cached_video = repository.get_processed_video("dQw4w9WgXcQ")

    assert cached_video is not None
    assert cached_video.video_id == "dQw4w9WgXcQ"
    assert cached_video.summary == "Summary"
    assert cached_video.twi_text == "Twi summary"
    assert cached_video.audio_data == b"mp3-bytes"
    assert cached_video.hit_count == 1
    assert cached_video.last_accessed_at is not None


def test_upsert_updates_existing_processed_video(tmp_path):
    """Should update an existing cache record without duplicating rows."""
    repository = make_repository(tmp_path)

    repository.upsert_processed_video(
        video_id="dQw4w9WgXcQ",
        source_url="https://youtu.be/dQw4w9WgXcQ",
        transcript="Old transcript",
        content_type="general",
        summary="Old summary",
        twi_text="Old Twi",
    )
    repository.upsert_processed_video(
        video_id="dQw4w9WgXcQ",
        source_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        transcript="New transcript",
        content_type="education",
        summary="New summary",
        twi_text="New Twi",
        audio_data=b"new-audio",
        audio_content_type="audio/mpeg",
    )

    with repository.session_scope() as session:
        videos = session.scalars(select(ProcessedVideo)).all()

    assert len(videos) == 1
    assert videos[0].transcript == "New transcript"
    assert videos[0].content_type == "education"
    assert videos[0].audio_data == b"new-audio"


def test_request_log_lifecycle(tmp_path):
    """Should create and complete request logs."""
    repository = make_repository(tmp_path)

    log_id = repository.create_request_log(
        chat_id=12345,
        url="https://youtu.be/dQw4w9WgXcQ",
        video_id="dQw4w9WgXcQ",
    )
    repository.complete_request_log(log_id, status="success", cache_hit=True)

    with repository.session_scope() as session:
        log = session.get(RequestLog, log_id)

    assert log is not None
    assert log.chat_id == 12345
    assert log.video_id == "dQw4w9WgXcQ"
    assert log.status == "success"
    assert log.cache_hit is True
    assert log.completed_at is not None


def test_get_missing_processed_video_returns_none(tmp_path):
    """Should return None when a cached video does not exist."""
    repository = make_repository(tmp_path)

    assert repository.get_processed_video("missing-id") is None
