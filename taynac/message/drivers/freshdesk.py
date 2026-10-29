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
from freshdesk.v2 import errors as fd_errors
from oslo_config import cfg
from oslo_log import log as logging
import requests
from requests import adapters

from taynac.common import exceptions
from taynac.message.drivers import base


CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class TimeoutHTTPAdapter(adapters.HTTPAdapter):
    """HTTPAdapter that applies a default timeout to every request"""

    def __init__(self, timeout, *args, **kwargs):
        self.timeout = timeout
        super().__init__(*args, **kwargs)

    def send(self, request, **kwargs):
        if kwargs.get("timeout") is None:
            kwargs["timeout"] = self.timeout
        return super().send(request, **kwargs)


class FreshDeskDriver(base.MessagingDriver):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.api = fd_api.API(CONF.freshdesk.domain, CONF.freshdesk.key)
        # python-freshdesk doesn't support a timeout, so set one on its
        # underlying requests session
        self.api._session.mount(
            "https://", TimeoutHTTPAdapter(CONF.freshdesk.timeout)
        )

    def send_message(
        self, subject, body, recipient, cc=[], tags=[], backend_id=None
    ):
        """Send message as an outbound freshdesk email or ticket reply

        If a 'backend_id' is provided (i.e. for an existing ticket),
        this is a reply to that ticket. The recipient, subject and
        tags of the ticket will not be altered to match the call args.
        Only the body and cc's will be used.
        """

        if backend_id:
            try:
                ticket_id = int(backend_id)
            except ValueError:
                raise exceptions.MessageSendError(
                    f"Invalid Freshdesk ticket ID {backend_id}"
                )

        try:
            if backend_id:
                self._update_ticket(ticket_id, body, cc_emails=cc)
            else:
                ticket_id = self._create_ticket(
                    email=recipient,
                    cc_emails=cc,
                    subject=subject,
                    body=self.format(subject, body),
                    tags=tags,
                    group_id=CONF.freshdesk.group_id,
                )
        except fd_errors.FreshdeskBadRequest as e:
            LOG.warning("Freshdesk rejected message to %s: %s", recipient, e)
            raise exceptions.MessageSendError(str(e))
        except fd_errors.FreshdeskRateLimited as e:
            LOG.warning(
                "Freshdesk rate limited message to %s: %s", recipient, e
            )
            raise exceptions.MessageBackendUnavailable(str(e))
        except requests.RequestException as e:
            # Includes the remaining Freshdesk errors, which subclass
            # requests.HTTPError, as well as timeouts and connection errors
            LOG.error("Freshdesk request failed for %s: %s", recipient, e)
            raise exceptions.MessageBackendError(
                "Failed to send message via Freshdesk"
            )

        return {"backend_id": ticket_id}

    def _create_ticket(self, email, cc_emails, subject, body, tags, group_id):
        ticket = self.api.tickets.create_outbound_email(
            subject=subject,
            description=body,
            email=email,
            email_config_id=int(CONF.freshdesk.email_config_id),
            group_id=group_id,
            cc_emails=cc_emails,
            tags=tags,
        )
        ticket_id = ticket.id
        LOG.info(
            "Created ticket %s, requester=%s, cc=%s",
            ticket_id,
            email,
            cc_emails,
        )

        return ticket_id

    def _update_ticket(self, ticket_id, body, cc_emails):
        try:
            self.api.comments.create_reply(
                ticket_id, body=body, cc_emails=cc_emails
            )
        except fd_errors.FreshdeskNotFound:
            LOG.warning("Freshdesk ticket %s not found", ticket_id)
            raise exceptions.MessageNotFound(f"Ticket {ticket_id} not found")
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
