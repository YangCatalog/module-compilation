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
    """This class serves to automatically email a group of admin/developers."""

    def __init__(
            self,
            config_path=os.environ['YANGCATALOG_CONFIG_PATH'],
            close_connection_after_message_sending: bool = True,
    ):
        config = create_config(config_path)
        self._email_from = config.get('Message-Section', 'email-from')
        self._is_production = config.get('General-Section', 'is-prod') == 'True'
        self._email_to = config.get('Message-Section', 'email-to').split()
        self._developers_email = config.get('Message-Section', 'developers-email').split()
        self._temp_dir = config.get('Directory-Section', 'temp')
        self._me = config.get('Web-Section', 'domain-prefix').split('/')[-1]
        self._smtp = smtplib.SMTP('localhost')
        self._close_connection_after_message_sending = close_connection_after_message_sending

    def __del__(self):
        if not self._close_connection_after_message_sending:
            self._smtp.quit()

    def _post_to_email(self, message: str, email_to: t.Optional[list] = None, subject: t.Optional[str] = None):
        """Send message to the list of e-mails.

            Arguments:
                :param message      (str) message to send
                :param email_to     (list) list of emails to send the message to
        """
        send_to = email_to or self._email_to
        msg = MIMEText(f'{message}\n\nMessage sent from {self._me}')
        msg['Subject'] = subject or 'Automatic generated message - RFC IETF'
        msg['From'] = self._email_from
        msg['To'] = ', '.join(send_to)

        if not self._is_production:
            print(f'You are in local env. Skip sending message to emails. The message was {msg}')
            self._smtp.quit()
            return
        self._smtp.sendmail(self._email_from, send_to, msg.as_string())
        if self._close_connection_after_message_sending:
            self._smtp.quit()

    def send_missing_modules(self, modules_list: list, incorrect_revision_modules: list):
        message = 'Following modules extracted from drafts are missing in YANG Catalog:\n'
        path = os.path.join(
            self._temp_dir, 'drafts-missing-modules/yangmodels/yang/experimental/ietf-extracted-YANG-modules',
        )
        for module in modules_list:
            message += f'{module}\n'
        message += f'\nAll missing modules have been copied to the directory: {path}'

        if incorrect_revision_modules:
            message += '\n\nFollowing missing modules do not have revision in the correct format:\n'
            for module in incorrect_revision_modules:
                message += f'{module}\n'

        self._post_to_email(message, self._developers_email)

    def send_problematic_draft(self, email_to: list[str], draft_filename: str, errors: str):
        subject = f'{GREETINGS}, "{draft_filename}" had errors during an extraction'
        message = f'During a daily check of IETF drafts, some errors were found in "{draft_filename}":\n{errors}'
        self._post_to_email(message, email_to=email_to, subject=subject)
