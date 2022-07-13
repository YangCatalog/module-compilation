import os
import shutil

import requests

from create_config import create_config


def main():
    config = create_config()
    yangcatalog_api_prefix = config.get('Web-Section', 'yangcatalog-api-prefix')
    all_modules_dir = config.get('Directory-Section', 'save-file-dir')
    ietf_dir = config.get('Directory-Section', 'ietf-directory')
    orgs = ['ieee', 'ietf']
    ietf_dependencies_dir = os.path.join(ietf_dir, 'dependencies')
    os.makedirs(ietf_dependencies_dir, exist_ok=True)
    for org in orgs:
        url = '{}/search-filter'.format(yangcatalog_api_prefix)
        body = {'input': {'organization': org}}

        response = requests.post(url, json=body)
        resp_body = response.json()
        modules = resp_body.get('yang-catalog:modules', {}).get('module', [])

        for mod in modules:
            name = mod['name']
            revision = mod['revision']
            yang_file = '{}@{}.yang'.format(name, revision)
            yang_file_dir = os.path.join(all_modules_dir, yang_file)
            if os.path.exists(yang_file_dir):
                dst = os.path.join(ietf_dependencies_dir, yang_file)
                shutil.copy2(yang_file_dir, dst)


if __name__ == '__main__':
    main()
