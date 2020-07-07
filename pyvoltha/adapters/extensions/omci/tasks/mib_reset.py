#
# Copyright 2020 the original author or authors.
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
from .task import Task
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, failure, TimeoutError
from pyvoltha.adapters.extensions.omci.omci_defs import ReasonCodes, EntityOperations
from pyvoltha.adapters.extensions.omci.omci_me import OntDataFrame
from pyvoltha.adapters.extensions.omci.omci_cc import DEFAULT_OMCI_TIMEOUT

RC = ReasonCodes
OP = EntityOperations


class MibResetException(Exception):
    pass


class OmciMibResetRequest(Task):
    """
    OpenOMCI routine to request mib reset of an ONU
    """
    task_priority = Task.MAX_PRIORITY
    name = "ONU OMCI MibReset Task"
    # adopt the global default
    DEFAULT_OMCI_RESET_TIMEOUT = DEFAULT_OMCI_TIMEOUT

    def __init__(self, omci_agent, device_id, timeout=DEFAULT_OMCI_RESET_TIMEOUT):
        """
        Class initialization

        :param omci_agent: (OmciAdapterAgent) OMCI Adapter agent
        """
        super(OmciMibResetRequest, self).__init__(OmciMibResetRequest.name,
                                                omci_agent,
                                                device_id,
                                                priority=OmciMibResetRequest.task_priority,
                                                exclusive=True)
        self._device = omci_agent.get_device(device_id)
        self._timeout = timeout
        self._local_deferred = None

    def cancel_deferred(self):
        super(OmciMibResetRequest, self).cancel_deferred()

        d, self._local_deferred = self._local_deferred, None
        try:
            if d is not None and not d.called:
                d.cancel()
        except:
            pass

    def start(self):
        """ Start task """
        super(OmciMibResetRequest, self).start()
        self._local_deferred = reactor.callLater(0, self.perform_mib_reset)

    @inlineCallbacks
    def perform_mib_reset(self):
        """
        Perform the mib reset requests

        Depending on the ONU implementation, a response may not be returned. For this
        reason, a timeout is considered successful.
        """
        self.log.info('perform-mib-reset')

        try:
            frame = OntDataFrame().mib_reset()
            self.strobe_watchdog()
            results = yield self._device.omci_cc.send(frame, timeout=self._timeout, high_priority=True)

            status = results.fields['omci_message'].fields['success_code']
            self.log.debug('mib-reset-status', status=status)

            # Did it fail
            if status != RC.Success.value:
                msg = 'MibReset request failed with status {}'.format(status)
                raise MibResetException(msg)

            self.log.info('mib-reset-success')
            self.deferred.callback("mib-reset-success")

        except TimeoutError:
            self.log.info('timeout', msg='Request timeout is not considered an error')
            self.deferred.callback(None)

        except Exception as e:
            self.log.exception('perform-mib-reset', e=e)
            self.deferred.errback(failure.Failure(e))
