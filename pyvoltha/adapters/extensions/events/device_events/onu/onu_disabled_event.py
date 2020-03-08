# Copyright 2017-present Adtran, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import
from voltha_protos.events_pb2 import EventCategory, EventSubCategory, EventType
from pyvoltha.adapters.extensions.events.adapter_events import DeviceEventBase


class OnuDisabledEvent(DeviceEventBase):
    def __init__(self, event_mgr, device_id, pon_id, onu_serial_number,
                 reg_id, olt_serial_number, raised_ts, ipv4_address=None,
                 onu_id=None):
        super(OnuDisabledEvent, self).__init__(event_mgr, raised_ts, object_type='ONU',
                                             event='ONU_DISABLED',
                                             resource_id=pon_id,
                                             category=EventCategory.COMMUNICATION,
                                             sub_category=EventSubCategory.PON,
                                             )

        self._pon_id = pon_id
        self._onu_id = onu_id
        self._onu_serial_number = onu_serial_number
        self._device_id = device_id
        self._olt_serial_number = olt_serial_number
        self._host = ipv4_address
        self._reg_id = reg_id

    def get_context_data(self):
        data = {
            'pon-id': self._pon_id,
            'onu-id': self._onu_id,
            'serial-number': self._onu_serial_number,
            'olt_serial_number': self._olt_serial_number,
            'device_id': self._device_id,
            'registration_id': self._reg_id
        }
        if self._host is not None:
            data['host'] = self._host

        return data
