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

import copy
import operator
import socket
import sys

from keystoneauth1 import loading as ks_loading
from oslo_config import cfg
from oslo_log import log as logging


LOG = logging.getLogger(__name__)


default_opts = [
    cfg.StrOpt('auth_strategy', default='keystone',
               choices=['noauth',
                        'keystone',
                        'testing'],
               help="The auth strategy for API requests."),
    cfg.StrOpt('host',
               default=socket.gethostname()),
]

flask_opts = [
    cfg.StrOpt('secret_key',
               secret=True),
    cfg.StrOpt('host',
               default='0.0.0.0'),
    cfg.IntOpt('port',
               default=5000),
]

taynac_opts = [
    cfg.StrOpt('message_driver',
               default='freshdesk',
               choices=['freshdesk', 'logging'],
               help="Messaging driver to use")
]

freshdesk_opts = [
    cfg.StrOpt('domain'),
    cfg.StrOpt('key', secret=True),
    cfg.IntOpt('email_config_id'),
    cfg.IntOpt('group_id'),
]

cfg.CONF.register_opts(taynac_opts, group='taynac')
cfg.CONF.register_opts(freshdesk_opts, group='freshdesk')
cfg.CONF.register_opts(flask_opts, group='flask')
cfg.CONF.register_opts(default_opts)

logging.register_options(cfg.CONF)

ks_loading.register_auth_conf_options(cfg.CONF, 'service_auth')
ks_loading.register_session_conf_options(cfg.CONF, 'service_auth')


def init(args=[], conf_file='/etc/taynac/taynac.conf'):
    cfg.CONF(
        args,
        project='taynac',
        default_config_files=[conf_file])


def setup_logging(conf):
    """Sets up the logging options for a log with supplied name.

    :param conf: a cfg.ConfOpts object
    """
    product_name = "taynac"

    logging.setup(conf, product_name)
    LOG.info("Logging enabled!")
    LOG.debug("command line: %s", " ".join(sys.argv))


# Used by oslo-config-generator entry point
# https://docs.openstack.org/oslo.config/latest/cli/generator.html
def list_opts():
    return [
        ('DEFAULT', default_opts),
        ('taynac', taynac_opts),
        ('flask', flask_opts),
        ('freshdesk', freshdesk_opts),
        add_auth_opts(),
    ]


def add_auth_opts():
    opts = ks_loading.register_session_conf_options(cfg.CONF, 'service_auth')
    opt_list = copy.deepcopy(opts)
    opt_list.insert(0, ks_loading.get_auth_common_conf_options()[0])
    for plugin_option in ks_loading.get_auth_plugin_conf_options('password'):
        if all(option.name != plugin_option.name for option in opt_list):
            opt_list.append(plugin_option)
    opt_list.sort(key=operator.attrgetter('name'))
    return ('service_auth', opt_list)
