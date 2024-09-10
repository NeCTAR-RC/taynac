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


from flask import request
import flask_restful
import marshmallow
from oslo_config import cfg
from oslo_log import log as logging
from oslo_policy import policy

from taynac.api.v1.resources import base
from taynac.api.v1.schemas import message as schemas
from taynac.common import policies
from taynac.message import api

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class Message(base.Resource):

    POLICY_PREFIX = policies.MESSAGE_PREFIX

    def post(self, **kwargs):
        try:
            self.authorize('send')
        except policy.PolicyNotAuthorized:
            flask_restful.abort(403, message="Not authorised")
        try:
            json_data = request.get_json()
        except Exception:
            return {"message": "No input data provided"}, 400

        try:
            message = schemas.message.load(json_data)
        except marshmallow.ValidationError as err:
            return {"message": err.messages}, 422

        mapi = api.MessageAPI()
        data = mapi.send_message(message["subject"],
                                 message["body"],
                                 message["recipient"],
                                 message["cc"],
                                 tags=message.get("tags", []),
                                 backend_id=message.get("backend_id", None))

        return schemas.message_response.dump(data)
