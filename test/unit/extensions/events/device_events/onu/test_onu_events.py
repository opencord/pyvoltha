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
#

import arrow
from unittest import TestCase, main
from pyvoltha.adapters.kafka.core_proxy import CoreProxy
from pyvoltha.adapters.extensions.events.adapter_events import AdapterEvents
from pyvoltha.adapters.extensions.events.device_events.onu.onu_activation_fail_event import OnuActivationFailEvent
from pyvoltha.adapters.extensions.events.device_events.onu.onu_active_event import OnuActiveEvent
from pyvoltha.adapters.extensions.events.device_events.onu.onu_discovery_event import OnuDiscoveryEvent
from pyvoltha.adapters.extensions.events.device_events.onu.onu_dying_gasp_event import OnuDyingGaspEvent
from pyvoltha.adapters.extensions.events.device_events.onu.onu_equipment_event import OnuEquipmentEvent
from pyvoltha.adapters.extensions.events.device_events.onu.onu_high_rx_optical_power_event import OnuHighRxOpticalEvent
from pyvoltha.adapters.extensions.events.device_events.onu.onu_high_tx_optical_power_event import OnuHighTxOpticalEvent
from pyvoltha.adapters.extensions.events.device_events.onu.onu_laser_bias_current_event import OnuLaserBiasEvent
from pyvoltha.adapters.extensions.events.device_events.onu.onu_laser_eol_event import OnuLaserEolEvent
from pyvoltha.adapters.extensions.events.device_events.onu.onu_lob_event import OnuLobEvent
from pyvoltha.adapters.extensions.events.device_events.onu.onu_lopc_mic_error_event import OnuLopcMicErrorEvent
from pyvoltha.adapters.extensions.events.device_events.onu.onu_lopc_miss_event import OnuLopcMissEvent
from pyvoltha.adapters.extensions.events.device_events.onu.onu_los_event import OnuLosEvent
from pyvoltha.adapters.extensions.events.device_events.onu.onu_low_rx_optical_power_event import OnuLowRxOpticalEvent
from pyvoltha.adapters.extensions.events.device_events.onu.onu_low_tx_optical_power_event import OnuLowTxOpticalEvent
from pyvoltha.adapters.extensions.events.device_events.onu.onu_selftest_failure_event import OnuSelfTestFailureEvent
from pyvoltha.adapters.extensions.events.device_events.onu.onu_signal_degrade_event import OnuSignalDegradeEvent
from pyvoltha.adapters.extensions.events.device_events.onu.onu_signal_fail_event import OnuSignalFailEvent
from pyvoltha.adapters.extensions.events.device_events.onu.onu_startup_event import OnuStartupEvent
from pyvoltha.adapters.extensions.events.device_events.onu.onu_temp_red_event import OnuTempRedEvent
from pyvoltha.adapters.extensions.events.device_events.onu.onu_temp_yellow_event import OnuTempYellowEvent
from pyvoltha.adapters.extensions.events.device_events.onu.onu_voltage_red_event import OnuVoltageRedEvent
from pyvoltha.adapters.extensions.events.device_events.onu.onu_voltage_yellow_event import OnuVoltageYellowEvent
from pyvoltha.adapters.extensions.events.device_events.onu.onu_window_drift_event import OnuWindowDriftEvent

DEFAULT_ONU_DEVICE_ID = 'default_onu_mock'
DEFAULT_PON_ID = 0
DEFAULT_ONU_ID = 0
DEFAULT_ONU_SN = 'TEST00000001'
DEFAULT_OLT_SN = 'ABCDXXXXYYYY'
DEFAULT_ONU_REG = 'ABCD1234'

core_proxy = CoreProxy(
               kafka_proxy=None,
               default_core_topic='rwcore',
               default_event_topic='voltha.events',
               my_listening_topic='openonu')

event_mgr = AdapterEvents(core_proxy, DEFAULT_ONU_DEVICE_ID, DEFAULT_ONU_DEVICE_ID, DEFAULT_ONU_SN)


class TestOnuActivationFailEvent(TestCase):

    def setUp(self):
        self.event = OnuActivationFailEvent(event_mgr, DEFAULT_ONU_ID, DEFAULT_PON_ID, DEFAULT_ONU_SN,
                                            arrow.utcnow().timestamp)

    def test_get_context_data(self):
        expected_dict = {'onu-id': DEFAULT_ONU_ID,
                         'onu-intf-id': DEFAULT_PON_ID,
                         'onu-serial-number': DEFAULT_ONU_SN}

        self.assertEqual(self.event.get_context_data(), expected_dict)

class TestOnuActiveEvent(TestCase):

    def setUp(self):
        self.event = OnuActiveEvent(event_mgr, DEFAULT_ONU_DEVICE_ID, DEFAULT_PON_ID, DEFAULT_ONU_SN,
                                    DEFAULT_ONU_REG, DEFAULT_OLT_SN, arrow.utcnow().timestamp, onu_id=DEFAULT_ONU_ID )

    def test_get_context_data(self):

        expected_dict = {
            'pon-id': DEFAULT_PON_ID,
            'onu-id': DEFAULT_ONU_ID,
            'serial-number': DEFAULT_ONU_SN,
            'olt_serial_number': DEFAULT_OLT_SN,
            'device_id': DEFAULT_ONU_DEVICE_ID,
            'registration_id': DEFAULT_ONU_REG
        }

        self.assertEqual(self.event.get_context_data(), expected_dict)

class TestOnuDiscoveryEvent(TestCase):

        def setUp(self):
            self.event = OnuDiscoveryEvent(event_mgr, DEFAULT_PON_ID, DEFAULT_ONU_SN,
                                               arrow.utcnow().timestamp)
        def test_get_context_data(self):
            expected_dict = {'pon-id': DEFAULT_PON_ID,
                             'serial-number': DEFAULT_ONU_SN,
                             'device-type': 'onu'}

            self.assertEqual(self.event.get_context_data(), expected_dict)

class TestOnuDyingGaspEvent(TestCase):

    def setUp(self):
        self.event = OnuDyingGaspEvent(event_mgr, DEFAULT_ONU_ID, DEFAULT_PON_ID, DEFAULT_ONU_SN,
                                           arrow.utcnow().timestamp)

    def test_get_context_data(self):
        expected_dict = {'onu-id': DEFAULT_ONU_ID,
                         'onu-intf-id': DEFAULT_PON_ID,
                         'onu-serial-number': DEFAULT_ONU_SN}

        self.assertEqual(self.event.get_context_data(), expected_dict)


if __name__ == '__main__':
    main()
