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

import re

from keystoneauth1 import exceptions as ks_exc
from keystoneclient.v3 import client as ks_client
from oslo_config import cfg
from oslo_log import log as logging

from taynac.common import exceptions
from taynac.common import keystone

CONF = cfg.CONF
LOG = logging.getLogger(__name__)

EMAIL_RE = re.compile(r"[^@]+@[^@]+\.[^@]+")


def get_keystone_client():
    session = keystone.KeystoneSession().get_session()
    return ks_client.Client(session=session)


def _ref_id(ref):
    if isinstance(ref, dict):
        return ref.get("id")
    return ref


def get_project_recipients(project_id, client=None):
    """Resolve notification recipients for a keystone project.

    Returns a (recipient, cc) tuple: the primary recipient email and a
    sorted, deduplicated cc list excluding the primary, capped at
    [identity] cc_limit.

    The primary recipient is the first enabled tenant manager with a
    valid email address, falling back to the first such member when the
    project has no notifiable tenant managers.

    Raises ProjectNotFound if the project does not exist and
    NoRecipientsFound if no usable email address can be resolved.
    """
    if client is None:
        client = get_keystone_client()

    # role_assignments.list on a nonexistent project returns an empty
    # list rather than a 404, so check the project explicitly.
    try:
        client.projects.get(project_id)
    except ks_exc.NotFound:
        raise exceptions.ProjectNotFound(f"Project {project_id} not found")

    manager_role = CONF.identity.manager_role.lower()
    member_role = CONF.identity.member_role.lower()

    role_names = {}
    manager_ids = []
    member_ids = []
    # effective=True expands group assignments into their users
    for assignment in client.role_assignments.list(
        project=project_id, effective=True
    ):
        user_id = _ref_id(getattr(assignment, "user", None))
        role_id = _ref_id(getattr(assignment, "role", None))
        if not user_id or not role_id:
            continue

        if role_id not in role_names:
            role_names[role_id] = client.roles.get(role_id).name.lower()
        role_name = role_names[role_id]

        if role_name == manager_role and user_id not in manager_ids:
            manager_ids.append(user_id)
        elif role_name == member_role and user_id not in member_ids:
            member_ids.append(user_id)

    users = {}

    def _emails(user_ids):
        emails = []
        for user_id in user_ids:
            if user_id not in users:
                users[user_id] = client.users.get(user_id)
            user = users[user_id]
            if not getattr(user, "enabled", True):
                continue
            email = getattr(user, "email", None)
            if not email or not EMAIL_RE.match(email):
                continue
            email = email.lower()
            if email not in emails:
                emails.append(email)
        return emails

    ordered = _emails(manager_ids) + _emails(member_ids)
    if not ordered:
        raise exceptions.NoRecipientsFound(
            "No users with valid email addresses found for "
            f"project {project_id}"
        )

    recipient = ordered[0]
    cc = sorted(set(ordered) - {recipient})
    cc_limit = CONF.identity.cc_limit
    if len(cc) > cc_limit:
        LOG.warning(
            "Project %s has %d cc recipients, truncating to %d",
            project_id,
            len(cc),
            cc_limit,
        )
        cc = cc[:cc_limit]
    return recipient, cc
