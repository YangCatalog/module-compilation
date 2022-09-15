import typing as t
from configparser import ConfigParser

from redis import Redis

from create_config import create_config


class RedisUserNotificationsConnection:
    """
    A class for managing the Redis user notifications database.
    Used for querying emails unsubscribed from some notifications
    """

    def __init__(self, db: t.Optional[t.Union[int, str]] = None, config: ConfigParser = create_config()):
        self._redis_host = config.get('DB-Section', 'redis-host')
        self._redis_port = int(config.get('DB-Section', 'redis-port'))
        db = db if db is not None else config.get('DB-Section', 'redis-user-notifications-db', fallback=7)
        self.redis = Redis(host=self._redis_host, port=self._redis_port, db=db)

    def get_emails_unsubscribed_from_draft_errors_emails(self, draft_name_without_revision: str) -> list[str]:
        return list(map(lambda email: email.decode(), self.redis.smembers(draft_name_without_revision)))
