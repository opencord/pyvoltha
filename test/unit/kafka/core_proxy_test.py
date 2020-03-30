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
import os
import sys
from unittest import TestCase, main
from unittest.mock import patch
from twisted.internet import defer
from voltha_protos.adapter_pb2 import Adapter
from voltha_protos.device_pb2 import DeviceType

def mock_decorator(f):
    def real_wrapper(func):
        return func
    return real_wrapper


patch('pyvoltha.adapters.kafka.container_proxy.ContainerProxy.wrap_request', mock_decorator).start()
from pyvoltha.adapters.kafka.core_proxy import CoreProxy


class TestCoreProxy(TestCase):

    def setUp(self):
        self.core_proxy = CoreProxy(
            kafka_proxy=None,
            default_core_topic='test_core',
            default_event_topic='test.events',
            my_listening_topic='test_openonu')

    @defer.inlineCallbacks
    def test_register_defaults(self):
        adapter = Adapter(
            id="testAdapter",
            vendor="ONF",
            version="test",
        )
        supported_device_types = [
            DeviceType(
                id="brmc_openonu",
                vendor_ids=['BBSM'],
                adapter=adapter.id,
                accepts_bulk_flow_update=False,
                accepts_add_remove_flow_updates=True
            )
        ]

        expected_adapter = Adapter(
            id="testAdapter",
            vendor="ONF",
            version="test",
            currentReplica=1,
            totalReplicas=1
        )

        with patch.object(self.core_proxy, "invoke") as mock_invoke:

            mock_invoke.return_value = "success"

            res = yield self.core_proxy.register(adapter, supported_device_types)
            mock_invoke.assert_called_with(
                rpc="Register",
                adapter=expected_adapter,
                deviceTypes=supported_device_types
            )
            self.assertTrue(mock_invoke.call_count, 1)
            self.assertEqual(res, "success")

    @defer.inlineCallbacks
    def test_register_multiple(self):

        adapter = Adapter(
            id="testAdapter",
            vendor="ONF",
            version="test",
            currentReplica=4,
            totalReplicas=8
        )

        supported_device_types = [
            DeviceType(
                id="brmc_openonu",
                vendor_ids=['BBSM'],
                adapter=adapter.id,
                accepts_bulk_flow_update=False,
                accepts_add_remove_flow_updates=True
            )
        ]

        with patch.object(self.core_proxy, "invoke") as mock_invoke:
            mock_invoke.return_value = "success"

            res = yield self.core_proxy.register(adapter, supported_device_types)
            mock_invoke.assert_called_with(
                rpc="Register",
                adapter=adapter,
                deviceTypes=supported_device_types
            )


if __name__ == '__main__':
    main()
