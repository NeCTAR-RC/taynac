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

from oslo_config import cfg

from taynac.message.drivers import freshdesk
from taynac.tests.unit import base


CONF = cfg.CONF


@mock.patch('freshdesk.v2.api.API')
class FreshDeskDriverTests(base.TestCase):

    def test_api_send_new_message(self, mock_api):
        driver = freshdesk.FreshDeskDriver()
        mock_api.return_value.tickets.create_outbound_email.return_value = \
            mock.Mock(id=3)
        response = driver.send_message('subject-test',
                                        'description-text',
                                        'owner@fake.org',
                                        cc=['manager1@fake.org'],
                                        tags=['foo', 'bar'])

        mock_api.return_value.tickets.create_outbound_email.assert_called_with(
            subject='subject-test',
            description='description-text',
            email='owner@fake.org',
            email_config_id=int(CONF.freshdesk.email_config_id),
            group_id=456,
            cc_emails=['manager1@fake.org'],
            tags=['foo', 'bar']
        )
        self.assertEqual({'backend_id': 3}, response)

    def test_api_send_followup_message(self, mock_api):
        driver = freshdesk.FreshDeskDriver()
        response = driver.send_message('subject-test',
                                       'more text',
                                       'owner@fake.org',
                                       cc=['manager1@fake.org'],
                                       tags=['foo', 'bar'],
                                       backend_id=44)
        mock_api.return_value.comments.create_reply.assert_called_with(
            44, body='more text', cc_emails=['manager1@fake.org'])
        self.assertEqual({'backend_id': 44}, response)

    def test_create_ticket(self, mock_api):
        driver = freshdesk.FreshDeskDriver()
        mock_api.return_value.tickets.create_outbound_email.return_value = \
            mock.Mock(id=3)
        ticket_id = driver._create_ticket('owner@fake.org',
                                          ['manager1@fake.org'],
                                          'subject-test',
                                          'description-text',
                                          tags=['foo', 'bar'],
                                          group_id=99)

        mock_api.return_value.tickets.create_outbound_email.assert_called_with(
            subject='subject-test',
            description='description-text',
            email='owner@fake.org',
            email_config_id=int(CONF.freshdesk.email_config_id),
            group_id=99,
            cc_emails=['manager1@fake.org'],
            tags=['foo', 'bar']
        )
        self.assertEqual(3, ticket_id)

    def test_update_ticket_requester(self, mock_api):
        driver = freshdesk.FreshDeskDriver()
        driver._update_ticket_requester(43, 'owner@fake.org')
        mock_api.return_value.tickets.update_ticket.assert_called_with(
            43, email='owner@fake.org')

    def test_update_ticket(self, mock_api):
        driver = freshdesk.FreshDeskDriver()
        driver._update_ticket(44, 'some text', cc_emails=['manager1@fake.org'])
        mock_api.return_value.comments.create_reply.assert_called_with(
            44, body='some text', cc_emails=['manager1@fake.org']
        )

    def test_add_note_to_ticket(self, mock_api):
        driver = freshdesk.FreshDeskDriver()
        driver._add_note_to_ticket(1, 'note-update')
        mock_api.return_value.comments.create_note.assert_called_with(
            1, 'note-update')
