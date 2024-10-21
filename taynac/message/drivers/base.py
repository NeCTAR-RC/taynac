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

from oslo_config import cfg
from oslo_log import log as logging

import taynac
from taynac.common import exceptions

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


def get_jinja2_env():
    template_dir = CONF.taynac.template_dir or os.path.realpath(
        os.path.join(os.path.dirname(taynac.__file__), 'templates')
    )
    if not os.path.isdir(template_dir):
        raise exceptions.TemplateDirNotFound(
            f"Cannot find template_dir {template_dir}"
        )
    LOG.info(f"Getting Taynac templates from {template_dir}")
    return jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir))


class MessagingDriver:
    def send_message(
        self, subject, body, recipient, cc=[], tags=[], backend_id=None
    ):
        raise NotImplementedError

    def format(self, subject, body, template_name='envelope.tmpl') -> str:
        env = get_jinja2_env()
        try:
            template = env.get_template(template_name)
        except jinja2.TemplateNotFound:
            raise exceptions.TemplateNotFound(
                f"Cannot find template {template_name}"
            )

        return template.render({'subject': subject, 'body': body})
