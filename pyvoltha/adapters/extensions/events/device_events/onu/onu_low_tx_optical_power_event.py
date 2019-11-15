# Copyright 2018 the original author or authors.
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


class OnuLowTxOpticalEvent(DeviceEventBase):
    """
    The ONU Low Tx Optical Power Event is reported by the ANI-G (ME # 263) to
    indicate that the transmit optical power below lower threshold

    For ANI-G equipment events, the intf_id reported is that of the PON/ANI
    physical port number
    """
    def __init__(self, event_mgr, onu_id, intf_id, serial_number, raised_ts):
        super(OnuLowTxOpticalEvent, self).__init__(event_mgr, raised_ts, object_type='onu low tx optical power',
                                                   event='ONU_LOW_TX_OPTICAL',
                                                   category=EventCategory.COMMUNICATION,
                                                   sub_category=EventSubCategory.ONU)
        self._onu_id = onu_id
        self._intf_id = intf_id
        self._serial_number = serial_number

    def get_context_data(self):
        return {'onu-id': self._onu_id,
                'onu-intf-id': self._intf_id,
                'onu-serial-number': self._serial_number}
