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
from voltha_protos.events_pb2 import EventType, EventCategory, EventSubCategory
from pyvoltha.adapters.extensions.events.adapter_events import DeviceEventBase

class OnuDiscoveryEvent(DeviceEventBase):
    def __init__(self, event_mgr, pon_id, serial_number, raised_ts):
        super(OnuDiscoveryEvent, self).__init__(event_mgr, raised_ts, object_type='ONU Discovery',
                                                event='ONU_DISCOVERY',
                                                resource_id=pon_id,
                                                category=EventCategory.EQUIPMENT,
                                                sub_category=EventSubCategory.ONU)
        self._pon_id = pon_id
        self._serial_number = serial_number

    def get_context_data(self):
        return {
            'pon-id': self._pon_id,
            'serial-number': self._serial_number,
            'device-type': 'onu'
        }
