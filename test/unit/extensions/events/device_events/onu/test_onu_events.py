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

from __future__ import absolute_import
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

class TestOnuEquipmentEvent(TestCase):

    def setUp(self):
        self.event = OnuEquipmentEvent(event_mgr, DEFAULT_ONU_ID, DEFAULT_PON_ID, DEFAULT_ONU_SN,
                                           arrow.utcnow().timestamp)

    def test_get_context_data(self):
        expected_dict = {'onu-id': DEFAULT_ONU_ID,
                         'onu-intf-id': DEFAULT_PON_ID,
                         'onu-serial-number': DEFAULT_ONU_SN}

        self.assertEqual(self.event.get_context_data(), expected_dict)

class TestOnuHighRxOpticalEvent(TestCase):

    def setUp(self):
        self.event = OnuHighRxOpticalEvent(event_mgr, DEFAULT_ONU_ID, DEFAULT_PON_ID, DEFAULT_ONU_SN,
                                           arrow.utcnow().timestamp)

    def test_get_context_data(self):
        expected_dict = {'onu-id': DEFAULT_ONU_ID,
                         'onu-intf-id': DEFAULT_PON_ID,
                         'onu-serial-number': DEFAULT_ONU_SN}

        self.assertEqual(self.event.get_context_data(), expected_dict)

class TestOnuHighTxOpticalEvent(TestCase):

    def setUp(self):
        self.event = OnuHighTxOpticalEvent(event_mgr, DEFAULT_ONU_ID, DEFAULT_PON_ID, DEFAULT_ONU_SN,
                                           arrow.utcnow().timestamp)

    def test_get_context_data(self):
        expected_dict = {'onu-id': DEFAULT_ONU_ID,
                         'onu-intf-id': DEFAULT_PON_ID,
                         'onu-serial-number': DEFAULT_ONU_SN}

        self.assertEqual(self.event.get_context_data(), expected_dict)

class TestOnuLaserBiasEvent(TestCase):

    def setUp(self):
        self.event = OnuLaserBiasEvent(event_mgr, DEFAULT_ONU_ID, DEFAULT_PON_ID, DEFAULT_ONU_SN,
                                           arrow.utcnow().timestamp)

    def test_get_context_data(self):
        expected_dict = {'onu-id': DEFAULT_ONU_ID,
                         'onu-intf-id': DEFAULT_PON_ID,
                         'onu-serial-number': DEFAULT_ONU_SN}

        self.assertEqual(self.event.get_context_data(), expected_dict)

class TestOnuLaserEolEvent(TestCase):

    def setUp(self):
        self.event = OnuLaserEolEvent(event_mgr, DEFAULT_ONU_ID, DEFAULT_PON_ID, DEFAULT_ONU_SN,
                                       arrow.utcnow().timestamp)

    def test_get_context_data(self):
        expected_dict = {'onu-id': DEFAULT_ONU_ID,
                         'onu-intf-id': DEFAULT_PON_ID,
                         'onu-serial-number': DEFAULT_ONU_SN}

        self.assertEqual(self.event.get_context_data(), expected_dict)

class TestOnuLobEvent(TestCase):

    def setUp(self):
        self.event = OnuLobEvent(event_mgr, DEFAULT_ONU_ID, DEFAULT_PON_ID, DEFAULT_ONU_SN,
                                       arrow.utcnow().timestamp)

    def test_get_context_data(self):
        expected_dict = {'onu-id': DEFAULT_ONU_ID,
                         'onu-intf-id': DEFAULT_PON_ID,
                         'onu-serial-number': DEFAULT_ONU_SN}

        self.assertEqual(self.event.get_context_data(), expected_dict)

class TestOnuLopcMicErrorEvent(TestCase):

    def setUp(self):
        self.event = OnuLopcMicErrorEvent(event_mgr, DEFAULT_ONU_ID, DEFAULT_PON_ID, DEFAULT_ONU_SN,
                                       arrow.utcnow().timestamp)

    def test_get_context_data(self):
        expected_dict = {'onu-id': DEFAULT_ONU_ID,
                         'onu-intf-id': DEFAULT_PON_ID,
                         'onu-serial-number': DEFAULT_ONU_SN}

        self.assertEqual(self.event.get_context_data(), expected_dict)

class TestOnuLopcMissEvent(TestCase):

    def setUp(self):
        self.event = OnuLopcMissEvent(event_mgr, DEFAULT_ONU_ID, DEFAULT_PON_ID, DEFAULT_ONU_SN,
                                       arrow.utcnow().timestamp)

    def test_get_context_data(self):
        expected_dict = {'onu-id': DEFAULT_ONU_ID,
                         'onu-intf-id': DEFAULT_PON_ID,
                         'onu-serial-number': DEFAULT_ONU_SN}

        self.assertEqual(self.event.get_context_data(), expected_dict)

class TestOnuLosEvent(TestCase):

    def setUp(self):
        self.event = OnuLosEvent(event_mgr, DEFAULT_ONU_ID, DEFAULT_PON_ID, DEFAULT_ONU_SN,
                                       arrow.utcnow().timestamp)

    def test_get_context_data(self):
        expected_dict = {'onu-id': DEFAULT_ONU_ID,
                         'onu-intf-id': DEFAULT_PON_ID,
                         'onu-serial-number': DEFAULT_ONU_SN}

        self.assertEqual(self.event.get_context_data(), expected_dict)

class TestOnuLowRxOpticalEvent(TestCase):

    def setUp(self):
        self.event = OnuLowRxOpticalEvent(event_mgr, DEFAULT_ONU_ID, DEFAULT_PON_ID, DEFAULT_ONU_SN,
                                       arrow.utcnow().timestamp)

    def test_get_context_data(self):
        expected_dict = {'onu-id': DEFAULT_ONU_ID,
                         'onu-intf-id': DEFAULT_PON_ID,
                         'onu-serial-number': DEFAULT_ONU_SN}

        self.assertEqual(self.event.get_context_data(), expected_dict)

class TestOnuLowTxOpticalEvent(TestCase):

    def setUp(self):
        self.event = OnuLowTxOpticalEvent(event_mgr, DEFAULT_ONU_ID, DEFAULT_PON_ID, DEFAULT_ONU_SN,
                                       arrow.utcnow().timestamp)

    def test_get_context_data(self):
        expected_dict = {'onu-id': DEFAULT_ONU_ID,
                         'onu-intf-id': DEFAULT_PON_ID,
                         'onu-serial-number': DEFAULT_ONU_SN}

        self.assertEqual(self.event.get_context_data(), expected_dict)

class TestOnuSelfTestFailureEvent(TestCase):

    def setUp(self):
        self.event = OnuSelfTestFailureEvent(event_mgr, DEFAULT_ONU_ID, DEFAULT_PON_ID, DEFAULT_ONU_SN,
                                       arrow.utcnow().timestamp)

    def test_get_context_data(self):
        expected_dict = {'onu-id': DEFAULT_ONU_ID,
                         'onu-intf-id': DEFAULT_PON_ID,
                         'onu-serial-number': DEFAULT_ONU_SN}

        self.assertEqual(self.event.get_context_data(), expected_dict)

class TestOnuSignalDegradeEvent(TestCase):

    def setUp(self):
        self.event = OnuSignalDegradeEvent(event_mgr, DEFAULT_ONU_ID, DEFAULT_PON_ID, 20, DEFAULT_ONU_SN,
                                       arrow.utcnow().timestamp)

    def test_get_context_data(self):
        expected_dict = {'onu-id': DEFAULT_ONU_ID,
                         'onu-intf-id': DEFAULT_PON_ID,
                         'onu-serial-number': DEFAULT_ONU_SN,
                         'inverse-bit-error-rate': 20}

        self.assertEqual(self.event.get_context_data(), expected_dict)

class TestOnuSignalFailEvent(TestCase):

    def setUp(self):
        self.event = OnuSignalFailEvent(event_mgr, DEFAULT_ONU_ID, DEFAULT_PON_ID, 20, DEFAULT_ONU_SN,
                                       arrow.utcnow().timestamp)

    def test_get_context_data(self):
        expected_dict = {'onu-id': DEFAULT_ONU_ID,
                         'onu-intf-id': DEFAULT_PON_ID,
                         'onu-serial-number': DEFAULT_ONU_SN,
                         'inverse-bit-error-rate': 20}

        self.assertEqual(self.event.get_context_data(), expected_dict)

class TestOnuStartupEvent(TestCase):

    def setUp(self):
        self.event = OnuStartupEvent(event_mgr, DEFAULT_ONU_ID, DEFAULT_PON_ID, DEFAULT_ONU_SN,
                                       arrow.utcnow().timestamp)

    def test_get_context_data(self):
        expected_dict = {'onu-id': DEFAULT_ONU_ID,
                         'onu-intf-id': DEFAULT_PON_ID,
                         'onu-serial-number': DEFAULT_ONU_SN}

        self.assertEqual(self.event.get_context_data(), expected_dict)

class TestOnuTempRedEvent(TestCase):

    def setUp(self):
        self.event = OnuTempRedEvent(event_mgr, DEFAULT_ONU_ID, DEFAULT_PON_ID, DEFAULT_ONU_SN,
                                       arrow.utcnow().timestamp)

    def test_get_context_data(self):
        expected_dict = {'onu-id': DEFAULT_ONU_ID,
                         'onu-intf-id': DEFAULT_PON_ID,
                         'onu-serial-number': DEFAULT_ONU_SN}

        self.assertEqual(self.event.get_context_data(), expected_dict)

class TestOnuTempYellowEvent(TestCase):

    def setUp(self):
        self.event = OnuTempYellowEvent(event_mgr, DEFAULT_ONU_ID, DEFAULT_PON_ID, DEFAULT_ONU_SN,
                                       arrow.utcnow().timestamp)

    def test_get_context_data(self):
        expected_dict = {'onu-id': DEFAULT_ONU_ID,
                         'onu-intf-id': DEFAULT_PON_ID,
                         'onu-serial-number': DEFAULT_ONU_SN}

        self.assertEqual(self.event.get_context_data(), expected_dict)

class TestOnuVoltageRedEvent(TestCase):

    def setUp(self):
        self.event = OnuVoltageRedEvent(event_mgr, DEFAULT_ONU_ID, DEFAULT_PON_ID, DEFAULT_ONU_SN,
                                       arrow.utcnow().timestamp)

    def test_get_context_data(self):
        expected_dict = {'onu-id': DEFAULT_ONU_ID,
                         'onu-intf-id': DEFAULT_PON_ID,
                         'onu-serial-number': DEFAULT_ONU_SN}

        self.assertEqual(self.event.get_context_data(), expected_dict)

class TestOnuVoltageYellowEvent(TestCase):

    def setUp(self):
        self.event = OnuVoltageYellowEvent(event_mgr, DEFAULT_ONU_ID, DEFAULT_PON_ID, DEFAULT_ONU_SN,
                                           arrow.utcnow().timestamp)

    def test_get_context_data(self):
        expected_dict = {'onu-id': DEFAULT_ONU_ID,
                         'onu-intf-id': DEFAULT_PON_ID,
                         'onu-serial-number': DEFAULT_ONU_SN}

        self.assertEqual(self.event.get_context_data(), expected_dict)

class TestOnuWindowDriftEvent(TestCase):

    def setUp(self):
        self.event = OnuWindowDriftEvent(event_mgr, DEFAULT_ONU_ID, DEFAULT_PON_ID, 10, 20, DEFAULT_ONU_SN,
                                           arrow.utcnow().timestamp)

    def test_get_context_data(self):
        expected_dict = {'onu-id': DEFAULT_ONU_ID,
                         'onu-intf-id': DEFAULT_PON_ID,
                         'onu-serial-number': DEFAULT_ONU_SN,
                         'drift': 10,
                         'new-eqd': 20}

        self.assertEqual(self.event.get_context_data(), expected_dict)


if __name__ == '__main__':
    main()
