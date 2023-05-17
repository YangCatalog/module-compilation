# Copyright The IETF Trust 2023, All Rights Reserved
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

__author__ = 'Bohdan Konovalenko'
__copyright__ = 'Copyright The IETF Trust 2023, All Rights Reserved'
__license__ = 'Apache License, Version 2.0'
__email__ = 'bohdan.konovalenko@pantheon.tech'

import os
import unittest
from unittest import mock

from message_factory import MessageFactory


class TestMessageFactory(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.resources = os.path.join(os.environ['TESTS_RESOURCES_DIR'], 'message_factory')

    @mock.patch('smtplib.SMTP')
    def test_send_missing_modules(self, smtp_mock: mock.MagicMock):
        message_factory = MessageFactory()
        message_factory._is_production = True
        message_factory.send_missing_modules(['test-module1.yang'], ['test_module2.yang'])
        smtp_mock.return_value.sendmail.assert_called()
        for call_args in smtp_mock.return_value.sendmail.call_args_list:
            message = call_args[0][2]
            self.assertIn('test-module1.yang', message)
            self.assertIn('test_module2.yang', message)

    @mock.patch('smtplib.SMTP')
    def test_send_problematic_draft(self, smtp_mock: mock.MagicMock):
        message_factory = MessageFactory()
        message_factory._is_production = True
        email_to = ['test_mail1@example.com', 'test_mail2@example.com']
        message_factory.send_problematic_draft(email_to=email_to, draft_filename='draft_filename.txt', errors='errors')
        smtp_mock.return_value.sendmail.assert_called()
        self.assertEqual(smtp_mock.return_value.sendmail.call_count, 2)
