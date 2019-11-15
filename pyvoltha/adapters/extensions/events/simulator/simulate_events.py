#
# Copyright 2017 the original author or authors.
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

from __future__ import absolute_import
import arrow
from pyvoltha.adapters.extensions.events.device_events.olt.olt_los_event import OltLosEvent
from pyvoltha.adapters.extensions.events.device_events.device_events.onu.onu_dying_gasp_event import OnuDyingGaspEvent
from pyvoltha.adapters.extensions.events.device_events.device_events.onu.onu_los_event import OnuLosEvent
from pyvoltha.adapters.extensions.events.device_events.device_events.onu.onu_lopc_miss_event import OnuLopcMissEvent
from pyvoltha.adapters.extensions.events.device_events.device_events.onu.onu_lopc_mic_error_event import OnuLopcMicErrorEvent
from pyvoltha.adapters.extensions.events.device_events.device_events.onu.onu_lob_event import OnuLobEvent
from pyvoltha.adapters.extensions.events.device_events.device_events.onu.onu_startup_event import OnuStartupEvent
from pyvoltha.adapters.extensions.events.device_events.device_events.onu.onu_signal_degrade_event import OnuSignalDegradeEvent
from pyvoltha.adapters.extensions.events.device_events.device_events.onu.onu_signal_fail_event import OnuSignalFailEvent
from pyvoltha.adapters.extensions.events.device_events.device_events.onu.onu_window_drift_event import OnuWindowDriftEvent
from pyvoltha.adapters.extensions.events.device_events.device_events.onu.onu_activation_fail_event import OnuActivationFailEvent
from pyvoltha.adapters.extensions.events.device_events.onu.device_events.onu.onu_discovery_event import OnuDiscoveryEvent

class AdapterEventSimulator(object):
    def __init__(self, adapter_events):
        self.adapter_events = adapter_events

    def simulate_device_events(self, event):
        raised_ts = arrow.utcnow().timestamp 
        if event.indicator == "los":
            event_obj = OltLosEvent(self.adapter_events, intf_id=event.intf_id, port_type_name=event.port_type_name, raised_ts)
        elif event.indicator == "dying_gasp":
            event_obj = OnuDyingGaspEvent(self.adapter_events, onu_id=event.onu_device_id, intf_id=event.intf_id, raised_ts)
        elif event.indicator == "onu_los":
            event_obj = OnuLosEvent(self.adapter_events, onu_id=event.onu_device_id, intf_id=event.intf_idraised_ts, raised_ts)
        elif event.indicator == "onu_lopc_miss":
            event_obj = OnuLopcMissEvent(self.adapter_events, onu_id=event.onu_device_id, intf_id=event.intf_id, raised_ts)
        elif event.indicator == "onu_lopc_mic":
            event_obj = OnuLopcMicErrorEvent(self.adapter_events, onu_id=event.onu_device_id, intf_id=event.intf_id, raised_ts)
        elif event.indicator == "onu_lob":
            event_obj = OnuLobEvent(self.adapter_events, onu_id=event.onu_device_id, intf_id=event.intf_id, raised_ts)
        elif event.indicator == "onu_startup":
            event_obj = OnuStartupEvent(self.adapter_events, intf_id=event.intf_id, onu_id=event.onu_device_id, raised_ts)
        elif event.indicator == "onu_signal_degrade":
            event_obj = OnuSignalDegradeEvent(self.adapter_events, intf_id=event.intf_id, onu_id=event.onu_device_id,
                                  inverse_bit_error_rate=event.inverse_bit_error_rate, raised_ts)
        elif event.indicator == "onu_drift_of_window":
            event_obj = OnuWindowDriftEvent(self.adapter_events, intf_id=event.intf_id,
                                onu_id=event.onu_device_id,
                                drift=event.drift,
                                new_eqd=event.new_eqd, raised_ts)
        elif event.indicator == "onu_signal_fail":
            event_obj = OnuSignalFailEvent(self.adapter_events, intf_id=event.intf_id,
                               onu_id=event.onu_device_id,
                               inverse_bit_error_rate=event.inverse_bit_error_rate, raised_ts)
        elif event.indicator == "onu_activation":
            event_obj = OnuActivationFailEvent(self.adapter_events, intf_id=event.intf_id,
                                   onu_id=event.onu_device_id, raised_ts)
        elif event.indicator == "onu_discovery":
            event_obj = OnuDiscoveryEvent(self.adapter_events, pon_id=event.intf_id,
                                   serial_number=event.onu_serial_number, raised_ts)
        else:
            raise Exception("Unknown event indicator %s" % event.indicator)

        if event.operation == event.RAISE:
            event_obj.send(True)
        elif event.operation == event.CLEAR:
            event_obj.send(False)
        else:
            # This shouldn't happen
            raise Exception("Unknown event operation")
