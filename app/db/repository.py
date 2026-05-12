"""Repository layer for database operations."""

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy.orm import Session, sessionmaker

from app.db.database import SessionLocal
from app.db.models import ProcessedVideo, RequestLog
from app.utils.time import utc_now


class DatabaseRepository:
    """Data access methods for processed video cache and request logs."""

    def __init__(self, session_factory: sessionmaker[Session] = SessionLocal) -> None:
        self.session_factory = session_factory
        self._request_session: Session | None = None

    @contextmanager
    def request_scope(self) -> Generator[Session, None, None]:
        """Single transactional session for the entire request pipeline."""
        session = self.session_factory()
        self._request_session = session
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
            self._request_session = None

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """Fallback session scope when not in a request_scope."""
        if self._request_session is not None:
            yield self._request_session
            return
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def create_request_log(
        self,
        *,
        chat_id: int,
        url: str,
        video_id: str | None = None,
        status: str = "started",
    ) -> int:
        """Create and return a request log id."""
        with self.session_scope() as session:
            log = RequestLog(
                chat_id=chat_id,
                url=url,
                video_id=video_id,
                status=status,
            )
            session.add(log)
            session.flush()
            return log.id

    def complete_request_log(
        self,
        log_id: int,
        *,
        status: str,
        cache_hit: bool = False,
        error_message: str | None = None,
    ) -> None:
        """Mark a request log as complete."""
        with self.session_scope() as session:
            log = session.get(RequestLog, log_id)
            if not log:
                return
            log.status = status
            log.cache_hit = cache_hit
            log.error_message = error_message
            log.completed_at = utc_now()

    def get_processed_video(self, video_id: str) -> ProcessedVideo | None:
        """Return a detached cached processed video, if present."""
        with self.session_scope() as session:
            video = session.get(ProcessedVideo, video_id)
            if not video:
                return None
            video.hit_count += 1
            video.last_accessed_at = utc_now()
            session.flush()
            session.expunge(video)
            return video

    def upsert_processed_video(
        self,
        *,
        video_id: str,
        source_url: str,
        transcript: str,
        content_type: str,
        summary: str,
        twi_text: str,
        audio_data: bytes | None = None,
        audio_content_type: str | None = None,
    ) -> ProcessedVideo:
        """Insert or update a cached processed video."""
        with self.session_scope() as session:
            video = session.get(ProcessedVideo, video_id)
            if video is None:
                video = ProcessedVideo(
                    video_id=video_id,
                    source_url=source_url,
                    transcript=transcript,
                    content_type=content_type,
                    summary=summary,
                    twi_text=twi_text,
                    audio_data=audio_data,
                    audio_content_type=audio_content_type,
                )
                session.add(video)
            else:
                video.source_url = source_url
                video.transcript = transcript
                video.content_type = content_type
                video.summary = summary
                video.twi_text = twi_text
                video.audio_data = audio_data
                video.audio_content_type = audio_content_type
                video.updated_at = utc_now()

            session.flush()
            session.expunge(video)
            return video
