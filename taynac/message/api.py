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
#

from oslo_config import cfg
from oslo_log import log as logging
from stevedore import driver as stevedore_driver


CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class MessageAPI:
    def __init__(self):
        self.driver = stevedore_driver.DriverManager(
            namespace="taynac.message_driver",
            name=CONF.taynac.message_driver,
            invoke_on_load=True,
        ).driver

    def send_message(
        self, subject, body, recipient, cc=[], tags=[], backend_id=None
    ):
        return self.driver.send_message(
            subject=subject,
            body=body,
            recipient=recipient,
            cc=cc,
            tags=tags,
            backend_id=backend_id,
        )
