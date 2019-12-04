#
# Copyright 2020 the original author or authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from __future__ import absolute_import
from .mib_db_api import CREATED_KEY, MODIFIED_KEY
import json
from datetime import datetime
import structlog
from pyvoltha.common.utils.registry import registry
from pyvoltha.common.config.config_backend import EtcdStore
import six


class MibTemplateDb(object):

    BASE_PATH = 'service/voltha/omci_mibs/templates'
    TEMPLATE_PATH = '{}/{}/{}'

    def __init__(self, vendor_id, equipment_id, software_version, serial_number, mac_address):
        self.log = structlog.get_logger()
        self._jsonstring = b''

        # lookup keys
        self._vendor_id = vendor_id
        self._equipment_id = equipment_id
        self._software_version = software_version

        # replacement values
        self._serial_number = serial_number
        self._mac_address = mac_address

        self.args = registry('main').get_args()
        host, port = self.args.etcd.split(':', 1)
        self._kv_store = EtcdStore(host, port, MibTemplateDb.BASE_PATH)
        self.loaded = False
        self._load_template()

    def get_template_instance(self):
        # swap out tokens with specific data
        fixup = self._jsonstring.decode('ascii')
        fixup = fixup.replace('%SERIAL_NUMBER%', self._serial_number)
        fixup = fixup.replace('%MAC_ADDRESS%', self._mac_address)

        # convert to a dict() compatible with mib_db_dict
        newdb = self._load_from_json(fixup)
        now = datetime.utcnow()

        # populate timestamps as if it was mib uploaded
        for cls_id, cls_data in newdb.items():
            if isinstance(cls_id, int):
                for inst_id, inst_data in cls_data.items():
                    if isinstance(inst_id, int):
                        newdb[cls_id][inst_id][CREATED_KEY] = now
                        newdb[cls_id][inst_id][MODIFIED_KEY] = now

        return newdb

    def _load_template(self):
        path = self._get_template_path()
        try:
            self._jsonstring = self._kv_store[path]
            self.log.debug('found-template-data', path=path)
            self.loaded = True
        except KeyError:
            self.log.warn('no-template-found', path=path)

    def _get_template_path(self):
        if not isinstance(self._vendor_id, six.string_types):
            raise TypeError('Vendor ID is a string')

        if not isinstance(self._equipment_id, six.string_types):
            raise TypeError('Equipment ID is a string')

        if not isinstance(self._software_version, six.string_types):
            raise TypeError('Software Version is a string')

        fmt = MibTemplateDb.TEMPLATE_PATH
        return fmt.format(self._vendor_id, self._equipment_id, self._software_version)

    def _load_from_json(self, jsondata):

        def json_obj_parser(x):
            if isinstance(x, dict):
                results = dict()
                for (key, value) in x.items():
                    try:
                        key = int(key)
                    except (ValueError, TypeError):
                        pass

                    results.update({key: value})
                return results
            return x

        template_data = json.loads(jsondata, object_hook=json_obj_parser)
        return template_data
