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

from freshdesk.v2 import api as fd_api
from oslo_config import cfg
from oslo_log import log as logging

from taynac.drivers import base


CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class FreshDeskDriver(base.MessagingDriver):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.api = fd_api.API(CONF.freshdesk.domain, CONF.freshdesk.key)

    def send_message(self, subject, body, recipient, cc=[]):

        ticket_id = self._create_ticket(email=recipient,
                                        cc_emails=cc,
                                        subject=subject,
                                        body=body)

        return {'backend_id': ticket_id}

    def _create_ticket(self, email, cc_emails, subject, body, tags=[]):
        ticket = self.api.tickets.create_outbound_email(
            subject=subject,
            description=body,
            email=email,
            email_config_id=int(CONF.freshdesk.email_config_id),
            group_id=CONF.freshdesk.group_id,
            cc_emails=cc_emails,
            tags=tags)
        ticket_id = ticket.id
        LOG.info("Created ticket %s, requester=%s, cc=%s",
                 ticket_id, email, cc_emails)

        return ticket_id

    def _update_ticket(self, ticket_id, body, cc_emails=[]):
        self.api.comments.create_reply(ticket_id, body=body,
                                       cc_emails=cc_emails)
        LOG.info("Sent reply to ticket %s", ticket_id)

    def _update_ticket_requester(self, ticket_id, owner):
        """Update ticket owner

        Doesn't check if the owner has changed
        as it needs more api calls otherwise(get_ticket then get_contact)
        """
        self.api.tickets.update_ticket(ticket_id, email=owner)
        LOG.debug("Set ticket requester to %s", owner)

    def _add_note_to_ticket(self, ticket_id, text):
        self.api.comments.create_note(ticket_id, text)
        LOG.info("Added private note to ticket %s", ticket_id)
