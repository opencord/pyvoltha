#
# Copyright 2018 the original author or authors.
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
from __future__ import absolute_import, division
from .mib_db_api import *
from pyvoltha.adapters.extensions.omci.database.mib_db_ext import MibDbExternal, MibDbStatistic
from pyvoltha.adapters.common.kvstore.etcd_store import EtcdStore
from pyvoltha.common.utils.registry import registry


class AlarmDbExternal(MibDbExternal):
    """
    A persistent external OpenOMCI Alarm Database
    """
    CURRENT_VERSION = 1                       # VOLTHA v1.3.0 release
    ALARM_BITMAP_KEY = 'alarm_bit_map'

    _TIME_FORMAT = '%Y%m%d-%H%M%S.%f'

    ALARM_PATH = 'service/voltha/omci_alarms'
    DEVICE_PATH = '{}'  # .format(device_id)
    CLASS_PATH = DEVICE_PATH + '/classes/{}'  # .format(device_id, class_id)

    def __init__(self, omci_agent):
        """
        Class initializer
        :param omci_agent: (OpenOMCIAgent) OpenOMCI Agent
        """
        super(AlarmDbExternal, self).__init__(omci_agent)
        self._core = omci_agent.core_proxy
        # Some statistics to help with debug/tuning/...
        self._statistics = {
            'get': MibDbStatistic('get'),
            'set': MibDbStatistic('set'),
            'create': MibDbStatistic('create'),
            'delete': MibDbStatistic('delete')
        }
        self.args = registry('main').get_args()
        host, port = self.args.etcd.split(':', 1)
        self._kv_store = EtcdStore(host, port, AlarmDbExternal.ALARM_PATH)

    def _get_device_path(self, device_id):
        return AlarmDbExternal.DEVICE_PATH.format(device_id)

    def _get_class_path(self, device_id, class_id):
        if not self._started:
            raise DatabaseStateError('The Database is not currently active')

        if not 0 <= class_id <= 0xFFFF:
            raise ValueError('class-id is 0..0xFFFF')

        fmt = AlarmDbExternal.CLASS_PATH
        return fmt.format(device_id, class_id)

    def _time_to_string(self, time):
        return time.strftime(AlarmDbExternal._TIME_FORMAT) if time is not None else ''

    def _string_to_time(self, time):
        return datetime.strptime(time, AlarmDbExternal._TIME_FORMAT) if len(time) else None

    def _attribute_to_string(self, device_id, class_id, attr_name, value, old_value=None):
        """
        Convert an ME's attribute value to string representation

        :param value: (long) Alarm bitmaps are always a Long
        :return: (str) String representation of the value
        """
        self.log.debug("attribute-to-string", device_id=device_id, class_id=class_id,
                       attr_name=attr_name, value=value)
        return str(value)

    def _string_to_attribute(self, device_id, class_id, attr_name, str_value):
        """
        Convert an Alarm ME's attribute value-string to its Scapy decode equivalent

        :param device_id: (str) ONU Device ID
        :param class_id: (int) Class ID
        :param attr_name: (str) Attribute Name (at this point only alarm_bit_map)
        :param str_value: (str) Attribute Value in string form

        :return: (int)  Long integer representation of the value
        """
        # Alarms are always a bitmap which is a long
        if attr_name == AlarmDbExternal.ALARM_BITMAP_KEY:
            value = int(str_value) if len(str_value) else 0
        else:
            value = 0

        self.log.debug("string-to-attribute", device_id=device_id, class_id=class_id,
                       attr_name=attr_name, value=value)
        return value
