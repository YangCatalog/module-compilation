import typing as t
from configparser import ConfigParser
from enum import Enum

from redis import Redis

from create_config import create_config


class EmailsUnsubscribingTypes(str, Enum):
    """Enum that contains names of sets with emails unsubscribed from specific types of emails"""
    ALL = 'unsubscribed_from_all_emails'
    DRAFTS = 'unsubscribed_from_draft_emails'


class RedisUsersConnection:
    """
    A class for managing the Redis user database.
    """

    def __init__(self, db: t.Optional[t.Union[int, str]] = None, config: ConfigParser = create_config()):
        self._redis_host = config.get('DB-Section', 'redis-host')
        self._redis_port = int(config.get('DB-Section', 'redis-port'))
        db = db if db is not None else config.get('DB-Section', 'redis-users-db', fallback=2)
        self.redis = Redis(host=self._redis_host, port=self._redis_port, db=db)

    def get_all_unsubscribed_emails(self, email_type: EmailsUnsubscribingTypes) -> list[str]:
        """Returns the list of all emails which are unsubscribed from particular email notifications"""
        return [email.decode() for email in self.redis.smembers(email_type)]
