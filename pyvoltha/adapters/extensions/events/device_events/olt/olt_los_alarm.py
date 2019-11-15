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

class OltLosEvent(DeviceEventBase):
    def __init__(self, event_mgr, intf_id, port_type_name, raised_ts):
        super(OltLosEvent, self).__init__(event_mgr, raised_ts, object_type='olt LOS',
                                          event='OLT_LOS',
                                          category=EventCategory.COMMUNICATION,
                                          sub_category=EventSubCategory.ONU)
        # Added port type to indicate if alarm was on NNI or PON
        self._intf_id = intf_id
        self._port_type_name = port_type_name

    def get_context_data(self):
        return {'olt-intf-id:': self._intf_id,
                'olt-port-type-name': self._port_type_name}
