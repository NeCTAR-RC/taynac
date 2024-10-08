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
from oslo_log import log as logging

from taynac.message.drivers import base


CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class LoggingDriver(base.MessagingDriver):
    def send_message(self, subject, body, recipient, cc=[], tags=[], **kwargs):
        LOG.info(
            "Sending message to %s, cc=%s " "Subject=%s message=%s tags=%s",
            recipient,
            cc,
            subject,
            body,
            tags,
        )
        return {"backend_id": None}
