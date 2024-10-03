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


from taynac.tests.unit import base


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

    def test_message_send_no_data(self):
        response = self.client.post("/v1/message/")
        self.assertStatus(response, 400)
        self.assertEqual(
            "No input data provided", response.get_json()["message"]
        )
