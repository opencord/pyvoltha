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
from voltha_protos.events_pb2 import EventCategory, EventSubCategory
from adapter_events import DeviceEventBase


class HeartbeatEvent(DeviceEventBase):
    def __init__(self, event_mgr, raised_ts, object_type='olt', heartbeat_misses=0):
        super(HeartbeatEvent, self).__init__(event_mgr, raised_ts, object_type,
                                             event='Heartbeat',
                                             category=EventCategory.EQUIPMENT,
                                             sub_category=ventSubCategory.PON)
        self._misses = heartbeat_misses

    def get_context_data(self):
        return {'heartbeats-missed': self._misses}
