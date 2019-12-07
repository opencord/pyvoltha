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
from twisted.internet.defer import inlineCallbacks, TimeoutError, failure, AlreadyCalledError, returnValue
from twisted.internet import reactor
from pyvoltha.adapters.extensions.omci.omci_defs import ReasonCodes
from pyvoltha.adapters.extensions.omci.omci_me import OntGFrame, Ont2GFrame, SoftwareImageFrame, IpHostConfigDataFrame
from pyvoltha.adapters.extensions.omci.database.mib_template_db import MibTemplateDb

RC = ReasonCodes


class MibTemplateTask(Task):
    """
    OpenOMCI MIB Template task

    On successful completion, this task will call the 'callback' method of the
    deferred returned by the start method.  If successful either a new mib db
    instance is returned or None, depending on if a template could be found.

    Its expected if None is returned the caller will perform a full MIB upload

    """
    task_priority = 250
    name = "MIB Template Task"

    def __init__(self, omci_agent, device_id):
        """
        Class initialization

        :param omci_agent: (OmciAdapterAgent) OMCI Adapter agent
        :param device_id: (str) ONU Device ID
        """
        super(MibTemplateTask, self).__init__(MibTemplateTask.name,
                                              omci_agent,
                                              device_id,
                                              priority=MibTemplateTask.task_priority)
        self._device = omci_agent.get_device(device_id)
        self._local_deferred = None

    def cancel_deferred(self):
        super(MibTemplateTask, self).cancel_deferred()

        d, self._local_deferred = self._local_deferred, None
        try:
            if d is not None and not d.called:
                d.cancel()
        except:
            pass

    def start(self):
        """
        Start MIB Template tasks
        """
        super(MibTemplateTask, self).start()
        self._local_deferred = reactor.callLater(0, self.create_template_instance)

    def stop(self):
        """
        Shutdown MIB Template tasks
        """
        self.log.debug('stopping')

        self.cancel_deferred()
        super(MibTemplateTask, self).stop()

    @inlineCallbacks
    def create_template_instance(self):
        """
        Gather unique identifying elements from the ONU.  Lookup template in persistent storage and return
        If no template is found return None so normal MIB Upload sequence can happen
        """
        self.log.debug('create-mib-template-instance')

        try:
            # MIB Reset start fresh
            self.strobe_watchdog()
            results = yield self._device.omci_cc.send_mib_reset()

            status = results.fields['omci_message'].fields['success_code']
            if status != ReasonCodes.Success.value:
                raise Exception('MIB Reset request failed with status code: {}'.format(status))

            self.log.debug('gather-onu-info')

            # Query for Vendor ID, Equipment ID and Software Version
            results = yield self._get_omci(OntGFrame(attributes=['vendor_id', 'serial_number']))
            self.log.debug('got-ontg', results=results)

            vendor_id = results.get('vendor_id', b'').decode('ascii').rstrip('\x00')
            serial_number = results.get('serial_number', '')

            results = yield self._get_omci(Ont2GFrame(attributes='equipment_id'))
            self.log.debug('got-ont2g', results=results)

            equipment_id = results.get('equipment_id', b'').decode('ascii').rstrip('\x00')

            # check only two software slots for active version.
            results1 = yield self._get_omci(SoftwareImageFrame(0, attributes=['is_active', 'version']))
            results2 = yield self._get_omci(SoftwareImageFrame(1, attributes=['is_active', 'version']))
            self.log.debug('got-software', results1=results1, results2=results2)

            software_version = ''
            if results1.get('is_active') == 1:
                software_version = results1.get('version', b'').decode('ascii').rstrip('\x00')
            elif results2.get('is_active') == 1:
                software_version = results2.get('version', b'').decode('ascii').rstrip('\x00')

            results = yield self._get_omci(IpHostConfigDataFrame(1, attributes='mac_address'))
            self.log.debug('got-ip-host-config', results=results)

            mac_address = results.get('mac_address', '')

            # Lookup template base on unique onu type info
            template = None
            found = False
            if vendor_id and equipment_id and software_version:
                self.log.debug('looking-up-template', vendor_id=vendor_id, equipment_id=equipment_id,
                               software_version=software_version)
                template = MibTemplateDb(vendor_id, equipment_id, software_version, serial_number, mac_address)
                found = yield template.load_template()
            else:
                self.log.info('no-usable-template-lookup-data', vendor_id=vendor_id, equipment_id=equipment_id,
                              software_version=software_version)

            if template and found:
                # generate db instance
                loaded_template_instance = template.get_template_instance()
                self.deferred.callback(loaded_template_instance)
            else:
                self.deferred.callback(None)

        except TimeoutError as e:
            self.log.warn('mib-template-timeout', e=e)
            self.deferred.errback(failure.Failure(e))

        except AlreadyCalledError:
            # Can occur if task canceled due to MIB Sync state change
            self.log.debug('already-called-exception')
            assert self.deferred.called, 'Unexpected AlreadyCalledError exception'
        except Exception as e:
            self.log.exception('mib-template', e=e)
            self.deferred.errback(failure.Failure(e))

    @inlineCallbacks
    def _get_omci(self, frame):
        self.strobe_watchdog()
        results = yield self._device.omci_cc.send(frame.get())

        results_fields = results.fields['omci_message'].fields
        status = results_fields['success_code']

        return_results = dict()
        if status == RC.Success.value:
            return_results = results_fields.get('data', dict())

        returnValue(return_results)
