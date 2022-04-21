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

import os
import smtplib
import typing as t
from email.mime.text import MIMEText

from create_config import create_config

GREETINGS = 'Hello from yang-catalog'


class MessageFactory:
    """This class serves to automatically send an email to a group of admin/developers.
    """

    def __init__(self, config_path=os.environ['YANGCATALOG_CONFIG_PATH']):
        config = create_config(config_path)
        self.__email_from = config.get('Message-Section', 'email-from')
        self.__is_production = config.get('General-Section', 'is-prod')
        self.__is_production = True if self.__is_production == 'True' else False
        self.__email_to = config.get('Message-Section', 'email-to').split()
        self.__developers_email = config.get('Message-Section', 'developers-email').split()
        self._temp_dir = config.get('Directory-Section', 'temp')
        self.__me = config.get('Web-Section', 'my-uri')
        self.__me = self.__me.split('/')[-1]
        self.__smtp = smtplib.SMTP('localhost')

    def __post_to_email(self, message: str, email_to: t.Optional[list] = None, subject: t.Optional[str] = None):
        """Send message to the list of e-mails.

            Arguments:
                :param message      (str) message to send
                :param email_to     (list) list of emails to send the message to
        """
        send_to = email_to if email_to else self.__email_to
        msg = MIMEText('{}\n\nMessage sent from {}'.format(message, self.__me))
        msg['Subject'] = subject if subject else 'Automatic generated message - RFC IETF'
        msg['From'] = self.__email_from
        msg['To'] = ', '.join(send_to)

        if not self.__is_production:
            print('You are in local env. Skip sending message to emails. The message was {}'.format(msg))
            self.__smtp.quit()
            return
        self.__smtp.sendmail(self.__email_from, send_to, msg.as_string())
        self.__smtp.quit()

    def send_missing_modules(self, modules_list: list, incorrect_revision_modules: list):
        message = ('Following modules extracted from drafts are missing in YANG Catalog:\n')
        path = os.path.join(self._temp_dir, 'drafts-missing-modules/yangmodels/yang/experimental/ietf-extracted-YANG-modules')
        for module in modules_list:
            message += '{}\n'.format(module)
        message += '\nAll missing modules have been copied to the directory: {}'.format(path)

        if incorrect_revision_modules:
            message += '\n\nFollowing missing modules do not have revision in the correct format:\n'
            for module in incorrect_revision_modules:
                message += '{}\n'.format(module)

        self.__post_to_email(message, self.__developers_email)
