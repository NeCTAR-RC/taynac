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


import jinja2
import os
from unittest import mock

from freshdesk.v2 import errors as fd_errors
from oslo_config import cfg
import requests

import taynac
from taynac.common import exceptions
from taynac.message.drivers import freshdesk
from taynac.tests.unit import base


CONF = cfg.CONF


def test_jinja2_env():
    """Create a jinja2 template env for testing."""

    test_template_dir = os.path.realpath(
        os.path.join(os.path.dirname(taynac.__file__), 'testing', 'templates')
    )
    return jinja2.Environment(
        loader=jinja2.FileSystemLoader(test_template_dir)
    )


@mock.patch("freshdesk.v2.api.API")
class FreshDeskDriverTests(base.TestCase):
    def test_api_send_new_message(self, mock_api):
        driver = freshdesk.FreshDeskDriver()
        mock_api.return_value.tickets.create_outbound_email.return_value = (
            mock.Mock(id=3)
        )
        with mock.patch(
            "taynac.message.drivers.base.get_jinja2_env",
            return_value=test_jinja2_env(),
        ):
            response = driver.send_message(
                "subject-test",
                "description-text",
                "owner@fake.org",
                cc=["manager1@fake.org"],
                tags=["foo", "bar"],
            )

        mock_api.return_value.tickets.create_outbound_email.assert_called_with(
            subject="subject-test",
            description="description-text\n"
            "<br>\n"
            "<br>\n"
            "<p>Here be sasquatches</p>",
            email="owner@fake.org",
            email_config_id=int(CONF.freshdesk.email_config_id),
            group_id=456,
            cc_emails=["manager1@fake.org"],
            tags=["foo", "bar"],
        )
        self.assertEqual({"backend_id": 3}, response)

    def test_api_send_followup_message(self, mock_api):
        driver = freshdesk.FreshDeskDriver()
        response = driver.send_message(
            "subject-test",
            "more text",
            "owner@fake.org",
            cc=["manager1@fake.org"],
            tags=["foo", "bar"],
            backend_id=44,
        )
        mock_api.return_value.comments.create_reply.assert_called_with(
            44, body="more text", cc_emails=["manager1@fake.org"]
        )
        self.assertEqual({"backend_id": 44}, response)

    def test_api_send_message_bad_request(self, mock_api):
        driver = freshdesk.FreshDeskDriver()
        error_message = (
            "Validation failed: [{'field': 'cc_emails', "
            "'message': 'Has 546 values, it can have maximum of 49 values', "
            "'code': 'invalid_value'}]"
        )
        mock_api.return_value.comments.create_reply.side_effect = (
            fd_errors.FreshdeskBadRequest(error_message)
        )
        with self.assertRaises(exceptions.MessageSendError) as cm:
            driver.send_message(
                "subject-test",
                "more text",
                "owner@fake.org",
                backend_id=44,
            )
        self.assertEqual(error_message, str(cm.exception))

    def test_api_send_message_invalid_backend_id(self, mock_api):
        driver = freshdesk.FreshDeskDriver()
        with self.assertRaisesRegex(
            exceptions.MessageSendError, "Invalid Freshdesk ticket ID abc"
        ):
            driver.send_message(
                "subject-test",
                "more text",
                "owner@fake.org",
                backend_id="abc",
            )
        mock_api.return_value.comments.create_reply.assert_not_called()

    def test_api_send_message_ticket_not_found(self, mock_api):
        driver = freshdesk.FreshDeskDriver()
        mock_api.return_value.comments.create_reply.side_effect = (
            fd_errors.FreshdeskNotFound("Freshdesk Request Failed")
        )
        with self.assertRaisesRegex(
            exceptions.MessageNotFound, "Ticket 44 not found"
        ):
            driver.send_message(
                "subject-test",
                "more text",
                "owner@fake.org",
                backend_id="44",
            )

    def test_api_send_message_rate_limited(self, mock_api):
        driver = freshdesk.FreshDeskDriver()
        mock_api.return_value.comments.create_reply.side_effect = (
            fd_errors.FreshdeskRateLimited("429 Rate Limit Exceeded")
        )
        with self.assertRaisesRegex(
            exceptions.MessageBackendUnavailable, "429 Rate Limit Exceeded"
        ):
            driver.send_message(
                "subject-test",
                "more text",
                "owner@fake.org",
                backend_id=44,
            )

    def test_api_send_message_backend_errors(self, mock_api):
        driver = freshdesk.FreshDeskDriver()
        create = mock_api.return_value.tickets.create_outbound_email
        for error in [
            fd_errors.FreshdeskUnauthorized("denied"),
            fd_errors.FreshdeskServerError("500: Server Error"),
            requests.Timeout("timed out"),
            requests.ConnectionError("refused"),
        ]:
            create.side_effect = error
            with mock.patch(
                "taynac.message.drivers.base.get_jinja2_env",
                return_value=test_jinja2_env(),
            ):
                with self.assertRaisesRegex(
                    exceptions.MessageBackendError,
                    "Failed to send message via Freshdesk",
                ):
                    driver.send_message(
                        "subject-test", "text", "owner@fake.org"
                    )

    def test_timeout_adapter_mounted(self, mock_api):
        CONF.set_override("timeout", 7, "freshdesk")
        freshdesk.FreshDeskDriver()
        mount = mock_api.return_value._session.mount
        mount.assert_called_once_with("https://", mock.ANY)
        self.assertEqual(7, mount.call_args[0][1].timeout)

    def test_create_ticket(self, mock_api):
        driver = freshdesk.FreshDeskDriver()
        mock_api.return_value.tickets.create_outbound_email.return_value = (
            mock.Mock(id=3)
        )
        ticket_id = driver._create_ticket(
            "owner@fake.org",
            ["manager1@fake.org"],
            "subject-test",
            "description-text",
            tags=["foo", "bar"],
            group_id=99,
        )

        mock_api.return_value.tickets.create_outbound_email.assert_called_with(
            subject="subject-test",
            description="description-text",
            email="owner@fake.org",
            email_config_id=int(CONF.freshdesk.email_config_id),
            group_id=99,
            cc_emails=["manager1@fake.org"],
            tags=["foo", "bar"],
        )
        self.assertEqual(3, ticket_id)

    def test_update_ticket_requester(self, mock_api):
        driver = freshdesk.FreshDeskDriver()
        driver._update_ticket_requester(43, "owner@fake.org")
        mock_api.return_value.tickets.update_ticket.assert_called_with(
            43, email="owner@fake.org"
        )

    def test_update_ticket(self, mock_api):
        driver = freshdesk.FreshDeskDriver()
        driver._update_ticket(44, "some text", cc_emails=["manager1@fake.org"])
        mock_api.return_value.comments.create_reply.assert_called_with(
            44, body="some text", cc_emails=["manager1@fake.org"]
        )

    def test_add_note_to_ticket(self, mock_api):
        driver = freshdesk.FreshDeskDriver()
        driver._add_note_to_ticket(1, "note-update")
        mock_api.return_value.comments.create_note.assert_called_with(
            1, "note-update"
        )


class TimeoutHTTPAdapterTests(base.TestCase):
    @mock.patch("requests.adapters.HTTPAdapter.send")
    def test_default_timeout(self, mock_send):
        adapter = freshdesk.TimeoutHTTPAdapter(5)
        adapter.send("request", timeout=None, verify=True)
        mock_send.assert_called_once_with("request", timeout=5, verify=True)

    @mock.patch("requests.adapters.HTTPAdapter.send")
    def test_explicit_timeout_kept(self, mock_send):
        adapter = freshdesk.TimeoutHTTPAdapter(5)
        adapter.send("request", timeout=2)
        mock_send.assert_called_once_with("request", timeout=2)
