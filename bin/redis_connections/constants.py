from enum import Enum


class RedisDatabasesDefaultsEnum(int, Enum):
    MODULES_DB = 1
    INCOMPLETE_MODULES_DB = 5
    USERS_NOTIFICATIONS_DB = 7
