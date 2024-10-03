#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from oslo_config import cfg

from taynac.message import api
from taynac.message.drivers import logging as logging_driver
from taynac.tests.unit import base


CONF = cfg.CONF


class MessageAPITests(base.TestCase):
    def test_init(self):
        message_api = api.MessageAPI()
        self.assertIsInstance(message_api.driver, logging_driver.LoggingDriver)
