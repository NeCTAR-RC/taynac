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

import flask_testing
from oslo_config import cfg
from oslo_context import context

from taynac import app
from taynac.common import keystone
from taynac import extensions

PROJECT_ID = 'ksprojectid1'
USER_ID = 'ksuserid1'


class TestCase(flask_testing.TestCase):

    def create_app(self):
        return app.create_app({
            'SECRET_KEY': 'secret',
            'TESTING': True,
        }, conf_file='taynac/tests/etc/taynac.conf')

    def setUp(self, *args, **kwargs):
        super().setUp(*args, **kwargs)
        self.addCleanup(mock.patch.stopall)
        self.context = context.RequestContext(user_id=USER_ID,
                                              project_id=PROJECT_ID)

    def tearDown(self, *args, **kwargs):
        super().tearDown(*args, **kwargs)
        cfg.CONF.reset()
        extensions.api.resources = []


class TestKeystoneWrapper(object):

    def __init__(self, app, roles):
        self.app = app
        self.roles = roles

    def __call__(self, environ, start_response):
        cntx = context.RequestContext(roles=self.roles,
                                      project_id=PROJECT_ID,
                                      user_id=USER_ID)
        environ[keystone.REQUEST_CONTEXT_ENV] = cntx

        return self.app(environ, start_response)


class ApiTestCase(TestCase):

    ROLES = ['member']

    def setUp(self):
        super().setUp()
        self.init_context()

    def init_context(self):
        self.app.wsgi_app = TestKeystoneWrapper(self.app.wsgi_app, self.ROLES)
