# Copyright The IETF Trust 2021, All Rights Reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

__author__ = 'Slavomir Mazur'
__copyright__ = 'Copyright The IETF Trust 2021, All Rights Reserved'
__license__ = 'Apache License, Version 2.0'
__email__ = 'slavomir.mazur@pantheon.tech'


import json
from configparser import ConfigParser

from redis import Redis

from create_config import create_config
from redis_connections.constants import RedisDatabasesEnum


class RedisConnection:
    def __init__(
        self,
        modules_db: int = RedisDatabasesEnum.MODULES_DB.value,
        config: ConfigParser = create_config(),
    ):
        self._redis_host = config.get('DB-Section', 'redis-host')
        self._redis_port = int(config.get('DB-Section', 'redis-port'))
        self.modules_db = Redis(host=self._redis_host, port=self._redis_port, db=modules_db)

    def populate_module(self, new_module: dict):
        """Create the redis key and set the module."""
        redis_key = self._create_module_key(new_module)
        self.set_module(new_module, redis_key)

    def get_module(self, key: str) -> str:
        data = self.modules_db.get(key)
        return (data or b'{}').decode('utf-8')

    def set_module(self, module: dict, redis_key: str):
        result = self.modules_db.set(redis_key, json.dumps(module))
        if result:
            print(f'{redis_key} key updated', flush=True)
        else:
            print(f'Problem while setting {redis_key}', flush=True)
        return result

    def _create_module_key(self, module: dict) -> str:
        return f'{module.get("name")}@{module.get("revision")}/{module.get("organization")}'
