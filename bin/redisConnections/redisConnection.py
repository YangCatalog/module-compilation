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

__author__ = "Slavomir Mazur"
__copyright__ = "Copyright The IETF Trust 2021, All Rights Reserved"
__license__ = "Apache License, Version 2.0"
__email__ = "slavomir.mazur@pantheon.tech"


import json

from create_config import create_config
from redis import Redis


class RedisConnection:

    def __init__(self, modules_db: int = 1):
        config = create_config()
        self.__redis_host = config.get('DB-Section', 'redis-host')
        self.__redis_port = config.get('DB-Section', 'redis-port')
        self.modulesDB = Redis(host=self.__redis_host, port=self.__redis_port, db=modules_db)

    ### MODULES DATABASE COMMUNICATION ###
    def update_module_properties(self, new_module: dict, existing_module: dict):
        keys = {**new_module, **existing_module}.keys()
        for key in keys:
            if key == 'implementations':
                new_impls = new_module.get('implementations', {}).get('implementation', [])
                existing_impls = existing_module.get('implementations', {}).get('implementation', [])
                existing_impls_names = [self.create_implementation_key(impl) for impl in existing_impls]
                for new_impl in new_impls:
                    new_impl_name = self.create_implementation_key(new_impl)
                    if new_impl_name not in existing_impls_names:
                        existing_impls.append(new_impl)
                        existing_impls_names.append(new_impl_name)
            elif key == 'dependents':
                new_prop_list = new_module.get(key, [])
                existing_prop_list = existing_module.get(key, [])
                existing_prop_names = [existing_prop.get('name') for existing_prop in existing_prop_list]
                for new_prop in new_prop_list:
                    new_prop_name = new_prop.get('name')
                    if new_prop_name not in existing_prop_names:
                        existing_prop_list.append(new_prop)
                        existing_prop_names.append(new_prop_name)
                    else:
                        index = existing_prop_names.index(new_prop_name)
                        existing_prop_list[index] = new_prop
            else:
                new_value = new_module.get(key)
                existing_value = existing_module.get(key)
                if existing_value != new_value and new_value is not None:
                    existing_module[key] = new_value

        return existing_module

    def populate_modules(self, new_modules: list):
        """ Merge new data of each module in "new_modules" list with existing data already stored in Redis.
        Set updated data to Redis under created key in format: <name>@<revision>/<organization>

        Argument:
            :param new_modules  (list) list of modules which need to be stored into Redis cache
        """
        new_merged_modules = {}

        for new_module in new_modules:
            redis_key = self.__create_module_key(new_module)
            redis_module = self.get_module(redis_key)
            if redis_module == '{}':
                updated_module = new_module
            else:
                updated_module = self.update_module_properties(new_module, json.loads(redis_module))

            self.set_redis_module(updated_module, redis_key)
            new_merged_modules[redis_key] = updated_module

    def get_module(self, key: str):
        data = self.modulesDB.get(key)
        return (data or b'{}').decode('utf-8')

    def set_redis_module(self, module: dict, redis_key: str):
        result = self.modulesDB.set(redis_key, json.dumps(module))

        return result

    def __create_module_key(self, module: dict):
        return '{}@{}/{}'.format(module.get('name'), module.get('revision'), module.get('organization'))

    def create_implementation_key(self, impl: dict):
        return '{}/{}/{}/{}'.format(impl['vendor'].replace(' ', '#'), impl['platform'].replace(' ', '#'),
                                    impl['software-version'].replace(' ', '#'), impl['software-flavor'].replace(' ', '#'))
