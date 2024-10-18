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

import taynac
from taynac.common import exceptions
from taynac.tests.unit import base


class DriverBaseTests(base.TestCase):
    def test_get_jinja2_env(self):
        env = taynac.message.drivers.base.get_jinja2_env()
        self.assertIsNotNone(env)

    @mock.patch('taynac.message.drivers.base.CONF')
    def test_get_jinja2_env_missing(self, mock_conf):
        mock_conf.taynac.template_dir = '/foo/bar'
        with self.assertRaisesRegex(
            exceptions.TemplateDirNotFound, 'Cannot find template_dir /foo/bar'
        ):
            taynac.message.drivers.base.get_jinja2_env()

    def test_base_unimplemented(self):
        driver = taynac.message.drivers.base.MessagingDriver()
        with self.assertRaises(NotImplementedError):
            driver.send_message('foo', 'bar', 'nobody@example.com')

    def test_format_missing(self):
        driver = taynac.message.drivers.base.MessagingDriver()
        with self.assertRaisesRegex(
            exceptions.TemplateNotFound, 'Cannot find template bzzz.tmpl'
        ):
            driver.format('stuff', 'bzzz.tmpl')
