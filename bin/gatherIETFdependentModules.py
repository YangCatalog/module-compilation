import shutil
from os import path

import requests

from create_config import create_config

if __name__ == '__main__':
    config = create_config()
    api_ip = config.get('Web-Section', 'ip')
    protocol = config.get('Web-Section', 'protocol-api')
    all_modules_dir = config.get('Directory-Section', 'save-file-dir')
    ietf_dir = config.get('Directory-Section', 'ietf-directory')
    orgs = ['ieee', 'ietf']
    for org in orgs:
        prefix = '{}://{}'.format(protocol, api_ip)
        url = '{}/api/search-filter'.format(prefix)
        body = {'input': {'organization': org}}

        response = requests.post(url, json=body)
        resp_body = response.json()
        modules = resp_body.get('yang-catalog:modules', {}).get('module', [])

        for mod in modules:
            name = mod['name']
            revision = mod['revision']
            yang_file = '{}@{}.yang'.format(name, revision)
            yang_file_dir = path.join(all_modules_dir, yang_file)
            if path.exists(yang_file_dir):
                shutil.copy2(yang_file_dir, '{}/dependencies/{}'.format(ietf_dir, yang_file))
