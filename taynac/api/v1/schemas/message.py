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

from taynac.extensions import ma

from marshmallow import fields


class MessageSchema(ma.Schema):

    subject = fields.Str(required=True)
    body = fields.Str(required=True)
    recipient = fields.Email(required=True)
    cc = fields.List(fields.Email(required=False), required=True)


message = MessageSchema()


class MessageResponseSchema(ma.Schema):

    backend_id = fields.Str(required=True)


message_response = MessageResponseSchema()
