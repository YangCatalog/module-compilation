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

from create_config import create_config
from redis import Redis


class RedisConnection:

    def __init__(self, modules_db: int = 1):
        config = create_config()
        self._redis_host = config.get('DB-Section', 'redis-host')
        self._redis_port = config.get('DB-Section', 'redis-port')
        self.modulesDB = Redis(host=self._redis_host, port=self._redis_port, db=modules_db)  # pyright: ignore

    def populate_module(self, new_module: dict):
        """Create the redis key and set the module."""
        redis_key = self._create_module_key(new_module)
        self.set_module(new_module, redis_key)

    def get_module(self, key: str):
        data = self.modulesDB.get(key)
        return (data or b'{}').decode('utf-8')

    def set_module(self, module: dict, redis_key: str):
        result = self.modulesDB.set(redis_key, json.dumps(module))
        if result:
            print('{} key updated'.format(redis_key), flush=True)
        else:
            print('Problem while setting {}'.format(redis_key), flush=True)

        return result

    def _create_module_key(self, module: dict):
        return '{}@{}/{}'.format(module.get('name'), module.get('revision'), module.get('organization'))
