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
from oslo_policy import policy


CONF = cfg.CONF
_POLICY_PATH = '/etc/taynac/policy.yaml'


enforcer = policy.Enforcer(CONF, policy_file=_POLICY_PATH)

ADMIN_OR_OWNER_OR_WRITER = 'admin_or_owner_or_writer'
ADMIN_OR_OWNER_OR_READER = 'admin_or_owner_or_reader'
ADMIN_OR_READER = 'admin_or_reader'
ADMIN_OR_WRITER = 'admin_or_writer'
ADMIN_OR_OWNER = 'admin_or_owner'


base_rules = [
    policy.RuleDefault(
        name='admin_required',
        check_str='role:admin or is_admin:1'),
    policy.RuleDefault(
        name='reader',
        check_str='role:reader or role:read_only '
                  'or role:cloud_admin or role:helpdesk'),
    policy.RuleDefault(
        name='writer',
        check_str='role:cloud_admin or role:helpdesk'),
    policy.RuleDefault(
        name='owner',
        check_str='project_id:%(project_id)s'),
    policy.RuleDefault(
        name=ADMIN_OR_OWNER,
        check_str='rule:admin_required or rule:owner'),
    policy.RuleDefault(
        name=ADMIN_OR_OWNER_OR_READER,
        check_str='rule:admin_or_owner or rule:reader'),
    policy.RuleDefault(
        name=ADMIN_OR_OWNER_OR_WRITER,
        check_str='rule:admin_or_owner or rule:writer'),
    policy.RuleDefault(
        name=ADMIN_OR_READER,
        check_str='rule:admin_required or rule:reader'),
    policy.RuleDefault(
        name=ADMIN_OR_WRITER,
        check_str='rule:admin_required or rule:writer'),
]

MESSAGE_PREFIX = "taynac:message:%s"

message_rules = [
    policy.DocumentedRuleDefault(
        name=MESSAGE_PREFIX % 'send',
        check_str='rule:admin_required',
        description='Send message.',
        operations=[{'path': '/v1/message/',
                     'method': 'POST'}]),
]

enforcer.register_defaults(base_rules)
enforcer.register_defaults(message_rules)


def list_rules():
    return base_rules + message_rules
