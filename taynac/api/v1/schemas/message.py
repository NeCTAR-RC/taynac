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
from marshmallow import validates_schema
from marshmallow import ValidationError


class MessageSchema(ma.Schema):
    subject = fields.Str(required=True)
    body = fields.Str(required=True)
    recipient = fields.Email()
    cc = fields.List(fields.Email(), load_default=[])
    tags = fields.List(fields.Str())
    backend_id = fields.Str()
    project_id = fields.Str()

    @validates_schema
    def validate_recipients(self, data, **kwargs):
        has_recipient = "recipient" in data
        has_project = "project_id" in data
        if has_recipient and has_project:
            raise ValidationError(
                "recipient and project_id are mutually exclusive",
                field_name="project_id",
            )
        if not has_recipient and not has_project:
            raise ValidationError(
                "One of recipient or project_id is required",
                field_name="recipient",
            )
        if has_project and data.get("cc"):
            raise ValidationError(
                "cc cannot be provided with project_id",
                field_name="cc",
            )


message = MessageSchema()


class MessageResponseSchema(ma.Schema):
    backend_id = fields.Str(required=True)
    recipient = fields.Email()
    cc = fields.List(fields.Email())


message_response = MessageResponseSchema()
