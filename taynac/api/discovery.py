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

import flask
import flask_restful


VERSIONS = [
    {
        "id": "v1",
        "status": "stable",
    }
]


class Versions(flask_restful.Resource):
    def get(self):
        base_url = flask.request.url_root
        versions = []
        for version in VERSIONS:
            v = dict(version)
            v["links"] = [
                {"rel": "self", "href": base_url + version["id"] + "/"}
            ]
            versions.append(v)
        return {"versions": {"values": versions}}, 300
