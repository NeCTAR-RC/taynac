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
from oslo_middleware import request_id

from taynac.common import keystone
from taynac.tests.unit import base


class AppTests(base.TestCase):
    def test_request_id_middleware_outermost(self):
        self.assertIsInstance(self.app.wsgi_app, request_id.RequestId)

    def test_request_id_header(self):
        response = self.client.get("/")
        self.assertIn("x-openstack-request-id", response.headers)


class KeystoneAppTests(base.TestCase):
    def create_app(self):
        cfg.CONF.set_override("auth_strategy", "keystone")
        return super().create_app()

    def test_middleware_order(self):
        wsgi_app = self.app.wsgi_app
        self.assertIsInstance(wsgi_app, request_id.RequestId)
        self.assertIsInstance(
            wsgi_app.application, keystone.SkippingAuthProtocol
        )
        self.assertIsInstance(
            wsgi_app.application._app, keystone.KeystoneContext
        )
