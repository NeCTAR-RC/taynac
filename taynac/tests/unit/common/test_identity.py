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
from oslo_config import cfg

from taynac.common import exceptions
from taynac.common import identity
from taynac.tests.unit import base

PROJECT_ID = "abc123"

MANAGER_ROLE = "manager-role-id"
MEMBER_ROLE = "member-role-id"
READER_ROLE = "reader-role-id"


class FakeRole:
    def __init__(self, name):
        self.name = name


ROLES = {
    MANAGER_ROLE: FakeRole("TenantManager"),
    MEMBER_ROLE: FakeRole("Member"),
    READER_ROLE: FakeRole("Reader"),
}


class FakeUser:
    def __init__(self, id, **kwargs):
        self.id = id
        for key, value in kwargs.items():
            setattr(self, key, value)


class FakeAssignment:
    def __init__(self, user_id=None, role_id=None):
        if user_id:
            self.user = {"id": user_id}
        if role_id:
            self.role = {"id": role_id}


def fake_client(assignments, users, project_exists=True):
    client = mock.Mock()
    if project_exists:
        client.projects.get.return_value = mock.Mock(id=PROJECT_ID)
    else:
        client.projects.get.side_effect = ks_exc.NotFound()
    client.role_assignments.list.return_value = assignments
    client.roles.get.side_effect = lambda role_id: ROLES[role_id]
    client.users.get.side_effect = lambda user_id: users[user_id]
    return client


class TestGetProjectRecipients(base.TestCase):
    def test_manager_is_primary_members_cc(self):
        client = fake_client(
            [
                FakeAssignment("u1", MANAGER_ROLE),
                FakeAssignment("u2", MEMBER_ROLE),
                FakeAssignment("u3", MEMBER_ROLE),
            ],
            {
                "u1": FakeUser("u1", email="manager@example.com"),
                "u2": FakeUser("u2", email="zeta@example.com"),
                "u3": FakeUser("u3", email="alpha@example.com"),
            },
        )
        recipient, cc = identity.get_project_recipients(
            PROJECT_ID, client=client
        )
        self.assertEqual("manager@example.com", recipient)
        self.assertEqual(["alpha@example.com", "zeta@example.com"], cc)
        client.role_assignments.list.assert_called_once_with(
            project=PROJECT_ID, effective=True
        )

    def test_second_manager_goes_to_cc(self):
        client = fake_client(
            [
                FakeAssignment("u1", MANAGER_ROLE),
                FakeAssignment("u2", MANAGER_ROLE),
            ],
            {
                "u1": FakeUser("u1", email="first@example.com"),
                "u2": FakeUser("u2", email="second@example.com"),
            },
        )
        recipient, cc = identity.get_project_recipients(
            PROJECT_ID, client=client
        )
        self.assertEqual("first@example.com", recipient)
        self.assertEqual(["second@example.com"], cc)

    def test_manager_without_email_falls_back_to_member(self):
        client = fake_client(
            [
                FakeAssignment("u1", MANAGER_ROLE),
                FakeAssignment("u2", MEMBER_ROLE),
            ],
            {
                "u1": FakeUser("u1"),
                "u2": FakeUser("u2", email="member@example.com"),
            },
        )
        recipient, cc = identity.get_project_recipients(
            PROJECT_ID, client=client
        )
        self.assertEqual("member@example.com", recipient)
        self.assertEqual([], cc)

    def test_no_managers_member_becomes_primary(self):
        client = fake_client(
            [
                FakeAssignment("u1", MEMBER_ROLE),
                FakeAssignment("u2", MEMBER_ROLE),
            ],
            {
                "u1": FakeUser("u1", email="one@example.com"),
                "u2": FakeUser("u2", email="two@example.com"),
            },
        )
        recipient, cc = identity.get_project_recipients(
            PROJECT_ID, client=client
        )
        self.assertEqual("one@example.com", recipient)
        self.assertEqual(["two@example.com"], cc)

    def test_duplicate_emails_deduplicated(self):
        client = fake_client(
            [
                FakeAssignment("u1", MANAGER_ROLE),
                FakeAssignment("u1", MEMBER_ROLE),
                FakeAssignment("u2", MEMBER_ROLE),
            ],
            {
                "u1": FakeUser("u1", email="manager@example.com"),
                "u2": FakeUser("u2", email="Manager@Example.com"),
            },
        )
        recipient, cc = identity.get_project_recipients(
            PROJECT_ID, client=client
        )
        self.assertEqual("manager@example.com", recipient)
        self.assertEqual([], cc)

    def test_disabled_users_excluded(self):
        client = fake_client(
            [
                FakeAssignment("u1", MANAGER_ROLE),
                FakeAssignment("u2", MEMBER_ROLE),
            ],
            {
                "u1": FakeUser(
                    "u1", email="manager@example.com", enabled=False
                ),
                "u2": FakeUser("u2", email="member@example.com"),
            },
        )
        recipient, cc = identity.get_project_recipients(
            PROJECT_ID, client=client
        )
        self.assertEqual("member@example.com", recipient)
        self.assertEqual([], cc)

    def test_missing_enabled_attribute_treated_as_enabled(self):
        client = fake_client(
            [FakeAssignment("u1", MANAGER_ROLE)],
            {"u1": FakeUser("u1", email="manager@example.com")},
        )
        recipient, cc = identity.get_project_recipients(
            PROJECT_ID, client=client
        )
        self.assertEqual("manager@example.com", recipient)

    def test_assignments_without_user_ref_skipped(self):
        client = fake_client(
            [
                FakeAssignment(role_id=MANAGER_ROLE),
                FakeAssignment(user_id="u1"),
                FakeAssignment("u2", MEMBER_ROLE),
            ],
            {"u2": FakeUser("u2", email="member@example.com")},
        )
        recipient, cc = identity.get_project_recipients(
            PROJECT_ID, client=client
        )
        self.assertEqual("member@example.com", recipient)
        self.assertEqual([], cc)

    def test_other_roles_ignored(self):
        client = fake_client(
            [
                FakeAssignment("u1", READER_ROLE),
                FakeAssignment("u2", MEMBER_ROLE),
            ],
            {
                "u1": FakeUser("u1", email="reader@example.com"),
                "u2": FakeUser("u2", email="member@example.com"),
            },
        )
        recipient, cc = identity.get_project_recipients(
            PROJECT_ID, client=client
        )
        self.assertEqual("member@example.com", recipient)
        self.assertEqual([], cc)

    def test_role_name_match_case_insensitive(self):
        cfg.CONF.set_override("manager_role", "TENANTMANAGER", "identity")
        client = fake_client(
            [FakeAssignment("u1", MANAGER_ROLE)],
            {"u1": FakeUser("u1", email="manager@example.com")},
        )
        recipient, cc = identity.get_project_recipients(
            PROJECT_ID, client=client
        )
        self.assertEqual("manager@example.com", recipient)

    def test_invalid_email_skipped(self):
        client = fake_client(
            [
                FakeAssignment("u1", MANAGER_ROLE),
                FakeAssignment("u2", MEMBER_ROLE),
            ],
            {
                "u1": FakeUser("u1", email="not-an-email"),
                "u2": FakeUser("u2", email="member@example.com"),
            },
        )
        recipient, cc = identity.get_project_recipients(
            PROJECT_ID, client=client
        )
        self.assertEqual("member@example.com", recipient)
        self.assertEqual([], cc)

    def test_email_lowercased(self):
        client = fake_client(
            [FakeAssignment("u1", MANAGER_ROLE)],
            {"u1": FakeUser("u1", email="Manager@Example.COM")},
        )
        recipient, cc = identity.get_project_recipients(
            PROJECT_ID, client=client
        )
        self.assertEqual("manager@example.com", recipient)

    def test_project_not_found_raises(self):
        client = fake_client([], {}, project_exists=False)
        self.assertRaises(
            exceptions.ProjectNotFound,
            identity.get_project_recipients,
            PROJECT_ID,
            client=client,
        )

    def test_no_recipients_raises(self):
        client = fake_client(
            [FakeAssignment("u1", MANAGER_ROLE)],
            {"u1": FakeUser("u1", enabled=False)},
        )
        self.assertRaises(
            exceptions.NoRecipientsFound,
            identity.get_project_recipients,
            PROJECT_ID,
            client=client,
        )

    def test_cc_capped_at_limit(self):
        cfg.CONF.set_override("cc_limit", 2, "identity")
        assignments = [FakeAssignment("u1", MANAGER_ROLE)]
        users = {"u1": FakeUser("u1", email="manager@example.com")}
        for i in range(5):
            user_id = f"m{i}"
            assignments.append(FakeAssignment(user_id, MEMBER_ROLE))
            users[user_id] = FakeUser(user_id, email=f"{user_id}@example.com")
        client = fake_client(assignments, users)
        recipient, cc = identity.get_project_recipients(
            PROJECT_ID, client=client
        )
        self.assertEqual("manager@example.com", recipient)
        self.assertEqual(["m0@example.com", "m1@example.com"], cc)

    def test_roles_and_users_fetched_once_per_id(self):
        client = fake_client(
            [
                FakeAssignment("u1", MANAGER_ROLE),
                FakeAssignment("u1", MEMBER_ROLE),
                FakeAssignment("u2", MEMBER_ROLE),
                FakeAssignment("u2", MANAGER_ROLE),
            ],
            {
                "u1": FakeUser("u1", email="one@example.com"),
                "u2": FakeUser("u2", email="two@example.com"),
            },
        )
        identity.get_project_recipients(PROJECT_ID, client=client)
        self.assertEqual(2, client.roles.get.call_count)
        self.assertEqual(2, client.users.get.call_count)
