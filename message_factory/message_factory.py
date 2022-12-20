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
import re
import smtplib
import typing as t
from email.mime.text import MIMEText

from create_config import create_config
from redis_connections.redis_user_notifications_connection import RedisUserNotificationsConnection

GREETINGS = 'Hello from yang-catalog'


class MessageFactory:
    """This class serves to automatically email a group of admin/developers."""

    def __init__(
        self,
        config_path=os.environ['YANGCATALOG_CONFIG_PATH'],
        close_connection_after_message_sending: bool = True,
        redis_user_notifications_connection: t.Optional[RedisUserNotificationsConnection] = None,
    ):
        config = create_config(config_path)
        self._email_from = config.get('Message-Section', 'email-from')
        self._is_production = config.get('General-Section', 'is-prod') == 'True'
        self._email_to = config.get('Message-Section', 'email-to').split()
        self._developers_email = config.get('Message-Section', 'developers-email').split()
        self._temp_dir = config.get('Directory-Section', 'temp')
        self._domain_prefix = config.get('Web-Section', 'domain-prefix')
        self._me = self._domain_prefix.split('/')[-1]

        self._smtp = smtplib.SMTP('localhost')
        self._close_connection_after_message_sending = close_connection_after_message_sending
        self._redis_user_notifications_connection = (
            redis_user_notifications_connection or RedisUserNotificationsConnection(config=config)
        )

    def __del__(self):
        if not self._close_connection_after_message_sending:
            self._smtp.quit()

    def send_missing_modules(self, modules_list: list, incorrect_revision_modules: list):
        message = 'Following modules extracted from drafts are missing in YANG Catalog:\n'
        path = os.path.join(
            self._temp_dir,
            'drafts-missing-modules/yangmodels/yang/experimental/ietf-extracted-YANG-modules',
        )
        for module in modules_list:
            message += f'{module}\n'
        message += f'\nAll missing modules have been copied to the directory: {path}'

        if incorrect_revision_modules:
            message += '\n\nFollowing missing modules do not have revision in the correct format:\n'
            for module in incorrect_revision_modules:
                message += f'{module}\n'

        self._post_to_email(message, self._developers_email)

    def send_problematic_draft(
        self,
        email_to: list[str],
        draft_filename: str,
        errors: str,
        draft_name_without_revision: t.Optional[str] = None,
    ):
        subject = f'{GREETINGS}, "{draft_filename}" had errors during an extraction'
        errors = errors.replace('\n', '<br>')
        message = f'During a daily check of IETF drafts, some errors were found in "{draft_filename}":<br><br>{errors}'
        draft_filename_without_format = draft_filename.split('.')[0]
        draft_name_without_revision = (
            draft_name_without_revision
            if draft_name_without_revision
            else re.sub(r'-\d+', '', draft_filename_without_format)
        )
        unsubscribed_emails = self._redis_user_notifications_connection.get_unsubscribed_emails(
            draft_name_without_revision,
        )
        email_to = [email for email in email_to if email not in unsubscribed_emails]
        message_subtype = 'html'
        for email in email_to:
            link_to_view_the_draft = (
                f'<a href="{self._domain_prefix}/yangvalidator?draft={draft_filename_without_format}">'
                'View it on YANG Catalog</a>'
            )
            unsubscribing_link = (
                f'<a href="{self._domain_prefix}/api/notifications/unsubscribe_from_emails/'
                f'{draft_name_without_revision}/{email}">unsubscribe</a>'
            )
            message = f'{message}<br><br>{link_to_view_the_draft} or {unsubscribing_link}'
            self._post_to_email(message, email_to=[email], subject=subject, subtype=message_subtype)

    def _post_to_email(
        self,
        message: str,
        email_to: t.Optional[list] = None,
        subject: t.Optional[str] = None,
        subtype: str = 'plain',
    ):
        """Send message to the list of e-mails.

        Arguments:
            :param message      (str) message to send
            :param email_to     (list) list of emails to send the message to
        """
        send_to = email_to or self._email_to
        newline_character = '<br>' if subtype == 'html' else '\n'
        msg = MIMEText(f'{message}{newline_character}{newline_character}Message sent from {self._me}', _subtype=subtype)
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
