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


class TestVersions(base.TestCase):
    def test_get_versions(self):
        response = self.client.get("/")
        self.assertStatus(response, 300)
        data = response.get_json()
        self.assertIn("versions", data)
        values = data["versions"]["values"]
        self.assertEqual(1, len(values))
        v1 = values[0]
        self.assertEqual("v1", v1["id"])
        self.assertEqual("stable", v1["status"])
        self.assertEqual(1, len(v1["links"]))
        self.assertEqual("self", v1["links"][0]["rel"])
        self.assertTrue(v1["links"][0]["href"].endswith("/v1/"))
