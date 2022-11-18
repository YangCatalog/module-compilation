import typing as t
from configparser import ConfigParser

from create_config import create_config
from redis import Redis
from redis_connections.constants import RedisDatabasesEnum


class RedisUserNotificationsConnection:
    """
    A class for managing the Redis user notifications database.
    Used for querying emails unsubscribed from some notifications
    """

    def __init__(self, db: t.Optional[t.Union[int, str]] = None, config: ConfigParser = create_config()):
        self._redis_host = config.get('DB-Section', 'redis-host')
        self._redis_port = int(config.get('DB-Section', 'redis-port'))
        db = db or config.get(
            'DB-Section',
            'redis-user-notifications-db',
            fallback=RedisDatabasesEnum.USERS_NOTIFICATIONS_DB.value,
        )
        self.redis = Redis(host=self._redis_host, port=self._redis_port, db=db)

    def get_unsubscribed_emails(self, emails_type: str) -> list[str]:
        return list(map(lambda email: email.decode(), self.redis.smembers(emails_type)))
