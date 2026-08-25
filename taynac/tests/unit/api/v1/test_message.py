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


from unittest import mock

from keystoneauth1 import exceptions as ks_exc

from taynac.common import exceptions
from taynac.tests.unit import base

RESOLVER = "taynac.api.v1.resources.message.identity.get_project_recipients"


class TestMessageAPI(base.ApiTestCase):
    def test_message_send(self):
        data = {
            "subject": "Test",
            "body": "Hi",
            "recipient": "test@test.test",
            "cc": ["test@test.com"],
        }
        response = self.client.post("/v1/message/", json=data)
        self.assert403(response)
        self.assertEqual("Not authorised", response.get_json()["message"])

    def test_message_send_project_id(self):
        data = {
            "subject": "Test",
            "body": "Hi",
            "project_id": "abc123",
        }
        response = self.client.post("/v1/message/", json=data)
        self.assert403(response)
        self.assertEqual("Not authorised", response.get_json()["message"])


class TestAdminMessageAPI(TestMessageAPI):
    ROLES = ["admin"]

    def test_message_send(self):
        data = {
            "subject": "Test",
            "body": "Hi",
            "recipient": "test@test.test",
            "cc": ["test@test.com"],
        }
        response = self.client.post("/v1/message/", json=data)
        self.assert200(response)
        self.assertIsNone(response.get_json()["backend_id"])

    def test_message_send_missing_data(self):
        data = {}
        response = self.client.post("/v1/message/", json=data)
        self.assertStatus(response, 422)
        self.assertEqual(
            ["Missing data for required field."],
            response.get_json()["message"]["subject"],
        )

    def test_message_send_error(self):
        data = {
            "subject": "Test",
            "body": "Hi",
            "recipient": "test@test.test",
            "cc": ["test@test.com"],
        }
        error_message = (
            "Validation failed: [{'field': 'cc_emails', "
            "'message': 'Has 546 values, it can have maximum of 49 values', "
            "'code': 'invalid_value'}]"
        )
        with mock.patch(
            "taynac.message.api.MessageAPI.send_message",
            side_effect=exceptions.MessageSendError(error_message),
        ):
            response = self.client.post("/v1/message/", json=data)
        self.assertStatus(response, 400)
        self.assertEqual(error_message, response.get_json()["message"])

    def test_message_send_no_data(self):
        response = self.client.post("/v1/message/")
        self.assertStatus(response, 400)
        self.assertEqual(
            "No input data provided", response.get_json()["message"]
        )

    def test_message_send_without_cc(self):
        data = {
            "subject": "Test",
            "body": "Hi",
            "recipient": "test@test.test",
        }
        response = self.client.post("/v1/message/", json=data)
        self.assert200(response)
        self.assertEqual([], response.get_json()["cc"])

    def test_message_send_project_id(self):
        data = {
            "subject": "Test",
            "body": "Hi",
            "project_id": "abc123",
        }
        with mock.patch(
            RESOLVER,
            return_value=(
                "manager@example.com",
                ["a@example.com", "b@example.com"],
            ),
        ) as mock_resolver:
            response = self.client.post("/v1/message/", json=data)
        mock_resolver.assert_called_once_with("abc123")
        self.assert200(response)
        json_data = response.get_json()
        self.assertEqual("manager@example.com", json_data["recipient"])
        self.assertEqual(["a@example.com", "b@example.com"], json_data["cc"])

    def test_message_send_project_id_and_recipient(self):
        data = {
            "subject": "Test",
            "body": "Hi",
            "recipient": "test@test.test",
            "project_id": "abc123",
        }
        response = self.client.post("/v1/message/", json=data)
        self.assertStatus(response, 422)
        self.assertEqual(
            ["recipient and project_id are mutually exclusive"],
            response.get_json()["message"]["project_id"],
        )

    def test_message_send_project_id_with_cc(self):
        data = {
            "subject": "Test",
            "body": "Hi",
            "project_id": "abc123",
            "cc": ["test@test.com"],
        }
        response = self.client.post("/v1/message/", json=data)
        self.assertStatus(response, 422)
        self.assertEqual(
            ["cc cannot be provided with project_id"],
            response.get_json()["message"]["cc"],
        )

    def test_message_send_no_recipient_or_project_id(self):
        data = {
            "subject": "Test",
            "body": "Hi",
        }
        response = self.client.post("/v1/message/", json=data)
        self.assertStatus(response, 422)
        self.assertEqual(
            ["One of recipient or project_id is required"],
            response.get_json()["message"]["recipient"],
        )

    def test_message_send_project_not_found(self):
        data = {
            "subject": "Test",
            "body": "Hi",
            "project_id": "abc123",
        }
        with mock.patch(
            RESOLVER,
            side_effect=exceptions.ProjectNotFound("Project abc123 not found"),
        ):
            response = self.client.post("/v1/message/", json=data)
        self.assertStatus(response, 400)
        self.assertEqual(
            "Project abc123 not found", response.get_json()["message"]
        )

    def test_message_send_project_no_recipients(self):
        data = {
            "subject": "Test",
            "body": "Hi",
            "project_id": "abc123",
        }
        with mock.patch(
            RESOLVER,
            side_effect=exceptions.NoRecipientsFound("No users found"),
        ):
            response = self.client.post("/v1/message/", json=data)
        self.assertStatus(response, 400)
        self.assertEqual("No users found", response.get_json()["message"])

    def test_message_send_keystone_error(self):
        data = {
            "subject": "Test",
            "body": "Hi",
            "project_id": "abc123",
        }
        with mock.patch(RESOLVER, side_effect=ks_exc.ConnectFailure("boom")):
            response = self.client.post("/v1/message/", json=data)
        self.assertStatus(response, 500)
        self.assertEqual(
            "Failed to resolve recipients from identity service",
            response.get_json()["message"],
        )
