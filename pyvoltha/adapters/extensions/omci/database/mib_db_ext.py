#
# Copyright 2018 the original author or authors.
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
from __future__ import absolute_import, division
from .mib_db_api import *
from voltha_protos.omci_mib_db_pb2 import MibInstanceData, MibClassData, \
    MibDeviceData, MibAttributeData, MessageType, ManagedEntity
from pyvoltha.adapters.extensions.omci.omci_entities import *
from pyvoltha.adapters.extensions.omci.omci_fields import *
from pyvoltha.adapters.common.kvstore.etcd_store import EtcdStore
from scapy.fields import StrField, FieldListField
from pyvoltha.common.utils.registry import registry
import six
from six.moves import range


class MibDbStatistic(object):
    """
    For debug/tuning purposes.

    With etcd around the Nov 8 time frame, (took out some created/modified settins) seeing the following:

        o Creates:  Avg: 141.4 mS, Min:  47 mS, Max: 323 mS    (148 samples)
        o Sets:     Avg: 206.4 mS, Min:  85 mS, Max: 781 mS    (142 samples)

    With etcd around the Nov 7 time frame, seeing the following:

        o Creates:  Avg: 124.4 mS, Min:  48 mS, Max: 531 mS    (148 samples)
        o Sets:     Avg: 210.7 mS, Min:  82 mS, Max: 944 mS    (140 samples)
        o Gets:     Avg:  10.9 mS, Min:   0 mS, Max: 384 mS    ( 99 samples)
        o Deletes:  No samples

    With etcd around the v1.5 time frame, seeing the following:

        o Creates:  Avg:  57.1 mS, Min:  76 mS, Max: 511 mS    (146 samples)
        o Sets:     Avg: 303.9 mS, Min: 126 mS, Max: 689 mS    (103 samples)
        o Gets:     Avg:   3.3 mS, Min:   0 mS, Max:   8 mS    (  9 samples)
        o Deletes:  No samples
    """

    def __init__(self, name):
        self._name = name
        self._count = 0
        self._total_time = 0  # Total milliseconds
        self._min_time = 99999999
        self._max_time = 0

    def get_statistics(self):
        return {
            'name': self._name,
            'count': self._count,
            'total_time': self._total_time,
            'min_time': self._min_time,
            'max_time': self._max_time,
            'avg_time': self._total_time / self._count if self._count > 0 else 0
        }

    def clear_statistics(self):
        self._count = 0
        self._total_time = 0  # Total milliseconds
        self._min_time = 99999999
        self._max_time = 0

    def increment(self, time):
        self._count += 1
        self._total_time += time  # Total milliseconds
        if self._min_time > time:
            self._min_time = time
        if self._max_time < time:
            self._max_time = time


class MibDbExternal(MibDbApi):
    """
    A persistent external OpenOMCI MIB Database
    """
    CURRENT_VERSION = 1

    _TIME_FORMAT = '%Y%m%d-%H%M%S.%f'

    # Paths from kv store
    MIB_PATH = 'service/voltha/omci_mibs'
    DEVICE_PATH = '{}'  # .format(device_id)
    CLASS_PATH = DEVICE_PATH + '/classes/{}'  # .format(device_id, class_id)

    def __init__(self, omci_agent):
        """
        Class initializer
        :param omci_agent: (OpenOMCIAgent) OpenOMCI Agent
        """
        super(MibDbExternal, self).__init__(omci_agent)
        self._core = omci_agent.core_proxy
        # Some statistics to help with debug/tuning/...
        self._statistics = {
            'get': MibDbStatistic('get'),
            'set': MibDbStatistic('set'),
            'create': MibDbStatistic('create'),
            'delete': MibDbStatistic('delete')
        }
        self.args = registry('main').get_args()
        host, port = self.args.etcd.split(':', 1)
        self._kv_store = EtcdStore(host, port, MibDbExternal.MIB_PATH)

    def start(self):
        """
        Start up/restore the database
        """
        self.log.debug('start')

        if not self._started:
            super(MibDbExternal, self).start()

            try:
                self.log.info('db-exists')
            except Exception as e:
                self.log.exception('start-failure', e=e)
                raise

    def stop(self):
        """
        Start up the database
        """
        self.log.debug('stop')

        if self._started:
            super(MibDbExternal, self).stop()
            # TODO: Delete this method if 6nothing else is done except calling the base class

    def add(self, device_id, overwrite=False):
        """
        Add a new ONU to database

        :param device_id: (str) Device ID of ONU to add
        :param overwrite: (bool) Overwrite existing entry if found.

        :raises KeyError: If device already exists and 'overwrite' is False
        """
        self.log.debug('add-device', device_id=device_id, overwrite=overwrite)

        now = datetime.utcnow()

        path = self._get_device_path(device_id)
        new_device_data = self._create_new_device(device_id)
        self.log.debug('new_device', new_device_data=new_device_data, device_id=device_id, path=path)

        try:
            search_device = self._kv_store.get(path)
            if search_device is None:
                # device not found, add new
                self._kv_store.set(path, new_device_data.SerializeToString())
                self._created = now
                self._modified = now
            else:
                # device is found
                if not overwrite:
                    # Device already exists
                    raise KeyError('Device with ID {} already exists in MIB database'.
                                   format(device_id))

                self._kv_store.set(path, new_device_data.SerializeToString())
                self._modified = now

        except Exception as e:
            self.log.exception('add-exception', device_id=device_id, e=e)
            raise

    def remove(self, device_id):
        """
        Remove an ONU from the database

        :param device_id: (str) Device ID of ONU to remove from database
        """
        self.log.debug('remove-device', device_id=device_id)

        if not self._started:
            raise DatabaseStateError('The Database is not currently active')

        if not isinstance(device_id, six.string_types):
            raise TypeError('Device ID should be an string')

        try:
            path = self._get_device_path(device_id)
            self._kv_store.delete(path)
            self._modified = datetime.utcnow()

        except Exception as e:
            self.log.exception('remove-exception', device_id=device_id, e=e)
            raise

    def set(self, device_id, class_id, entity_id, attributes):
        """
        Set a database value.  This should only be called by the MIB synchronizer
        and its related tasks

        :param device_id: (str) ONU Device ID
        :param class_id: (int) ME Class ID
        :param entity_id: (int) ME Entity ID
        :param attributes: (dict) Attribute dictionary

        :returns: (bool) True if the value was saved to the database. False if the
                         value was identical to the current instance

        :raises KeyError: If device does not exist
        :raises DatabaseStateError: If the database is not enabled
        """
        self.log.debug('set', device_id=device_id, class_id=class_id,
                       entity_id=entity_id, attributes=attributes)

        operation = 'set'
        start_time = datetime.utcnow()
        try:
            if not isinstance(device_id, six.string_types):
                raise TypeError('Device ID should be a string')

            if not 0 <= class_id <= 0xFFFF:
                raise ValueError("Invalid Class ID: {}, should be 0..65535".format(class_id))

            if not 0 <= entity_id <= 0xFFFF:
                raise ValueError("Invalid Instance ID: {}, should be 0..65535".format(entity_id))

            if not isinstance(attributes, dict):
                raise TypeError("Attributes should be a dictionary")

            if not self._started:
                raise DatabaseStateError('The Database is not currently active')

            class_path = self._get_class_path(device_id, class_id)
            class_data = MibClassData()
            query_data = self._kv_store.get(class_path)
            if query_data is None:
                # Here if the class-id does not yet exist in the database

                # This is needed to create a "slimmed down" reference to the class in the device object.
                # This would be used later if querying the entire device and needed to pull all the classes and instances
                new_class_data_ptr = self._create_new_class(device_id, class_id)
                dev_data = MibDeviceData()
                device_path = self._get_device_path(device_id)

                start_time = datetime.utcnow()
                query_data = self._kv_store.get(device_path)
                dev_data.ParseFromString(query_data)
                dev_data.classes.extend([new_class_data_ptr])

                self._kv_store.set(device_path, dev_data.SerializeToString())

                # Create fully populated class/entity instance data in its own place in the KV store
                new_class_data = self._create_new_class(device_id, class_id, entity_id,
                                                        attributes)

                self._kv_store.set(class_path, new_class_data.SerializeToString())

                return True
            else:
                # Here if the class-id exists in the database and we are updating instances or attributes
                class_data.ParseFromString(query_data)

                inst_data = next((inst for inst in class_data.instances
                                  if inst.instance_id == entity_id), None)

                modified = False
                new_data = None
                if inst_data is None:
                    # Creating a new instance
                    operation = 'create'
                    new_data = self._create_new_instance(device_id, class_id, entity_id, attributes)
                    modified = True
                else:
                    # Possibly adding to or updating an existing instance
                    new_data = self._update_existing_instance(device_id, class_id, entity_id, attributes, inst_data)
                    if new_data is not None:
                        modified = True

                if modified:
                    inst_index = next((index for index in range(len(class_data.instances)) if
                                       class_data.instances[index].instance_id == entity_id), None)
                    # Delete the old instance
                    if inst_index is not None:
                        del class_data.instances[inst_index]

                    # Add the new/updated instance
                    class_data.instances.extend([new_data])
                    self._kv_store.set(class_path, class_data.SerializeToString())

                return modified

        except Exception as e:
            self.log.exception('set-exception', device_id=device_id, class_id=class_id,
                               entity_id=entity_id, attributes=attributes, e=e)
            raise

        finally:
            if start_time is not None:
                diff = datetime.utcnow() - start_time
                # NOTE: Change to 'debug' when checked in, manually change to 'info'
                #       for development testing.
                self.log.debug('db-{}-time'.format(operation), milliseconds=diff.microseconds / 1000)
                self._statistics[operation].increment(diff.microseconds / 1000)

    def delete(self, device_id, class_id, entity_id):
        """
        Delete an entity from the database if it exists.  If all instances
        of a class are deleted, the class is deleted as well.

        :param device_id: (str) ONU Device ID
        :param class_id: (int) ME Class ID
        :param entity_id: (int) ME Entity ID

        :returns: (bool) True if the instance was found and deleted. False
                         if it did not exist.

        :raises KeyError: If device does not exist
        :raises DatabaseStateError: If the database is not enabled
        """
        self.log.debug('delete', device_id=device_id, class_id=class_id,
                       entity_id=entity_id)

        if not self._started:
            raise DatabaseStateError('The Database is not currently active')

        if not isinstance(device_id, six.string_types):
            raise TypeError('Device ID should be an string')

        if not 0 <= class_id <= 0xFFFF:
            raise ValueError('class-id is 0..0xFFFF')

        if not 0 <= entity_id <= 0xFFFF:
            raise ValueError('instance-id is 0..0xFFFF')

        start_time = datetime.utcnow()
        try:
            now = datetime.utcnow()
            class_path = self._get_class_path(device_id, class_id)
            class_data = MibClassData()
            query_data = self._kv_store.get(class_path)
            if query_data is not None:
                class_data.ParseFromString(query_data)

                inst_index = next((index for index in range(len(class_data.instances)) if
                                   class_data.instances[index].instance_id == entity_id), None)

                # Remove instance
                if inst_index is not None:
                    del class_data.instances[inst_index]
                    self._kv_store.set(class_path, class_data.SerializeToString())

                # If resulting class has no instance, remove it as well
                if len(class_data.instances) == 0:
                    self._kv_store.delete(class_path)

                    # Clean up Device class pointer
                    dev_data = MibDeviceData()
                    device_path = self._get_device_path(device_id)
                    query_data = self._kv_store.get(device_path)
                    dev_data.ParseFromString(query_data)

                    class_index = next((index for index in range(len(dev_data.classes)) if
                                        dev_data.classes[index].class_id == class_id), None)

                    if class_index is not None:
                        del dev_data.classes[class_index]
                        self._kv_store.set(device_path, dev_data.SerializeToString())

                self._modified = now
                return True
            else:
                self.log.warn('delete-key-not-found', device_id=device_id, class_id=class_id, entity_id=entity_id)
                return False  # Not found

        except Exception as e:
            self.log.exception('delete-exception', device_id=device_id, class_id=class_id, entity_id=entity_id, e=e)
            raise

        finally:
            diff = datetime.utcnow() - start_time
            # NOTE: Change to 'debug' when checked in, manually change to 'info'
            #       for development testing.
            self.log.debug('db-delete-time', milliseconds=diff.microseconds / 1000)
            self._statistics['delete'].increment(diff.microseconds / 1000)

    def query(self, device_id, class_id=None, instance_id=None, attributes=None):
        """
        Get database information.

        This method can be used to request information from the database to the detailed
        level requested

        :param device_id: (str) ONU Device ID
        :param class_id:  (int) Managed Entity class ID
        :param instance_id: (int) Managed Entity instance
        :param attributes: (list/set or str) Managed Entity instance's attributes

        :return: (dict) The value(s) requested. If class/inst/attribute is
                        not found, an empty dictionary is returned
        :raises KeyError: If the requested device does not exist
        :raises DatabaseStateError: If the database is not enabled
        """
        self.log.debug('query', device_id=device_id, class_id=class_id,
                       entity_id=instance_id, attributes=attributes)

        start_time = datetime.utcnow()
        end_time = None
        try:
            if class_id is None:
                # Get full device info.  This is painful given the recursive lookups involved!
                dev_data = MibDeviceData()
                device_path = self._get_device_path(device_id)
                query_data = self._kv_store.get(device_path)
                if query_data is not None:
                    dev_data.ParseFromString(query_data)

                    class_ids = [c.class_id for c in dev_data.classes]

                    class_data_dict = dict()
                    if len(class_ids):
                        for class_id in class_ids:
                            # Recursively call query with the class_id passed, so below can do what it already does
                            class_data_dict[class_id] = self.query(device_id, class_id)

                    end_time = datetime.utcnow()
                    data = self._device_to_dict(dev_data, class_data_dict)
                else:
                    self.log.debug('query-no-device', device_id=device_id)
                    data = dict()

            elif instance_id is None:
                # Get all instances of the class
                class_data = MibClassData()
                class_path = self._get_class_path(device_id, class_id)
                query_data = self._kv_store.get(class_path)
                if query_data is not None:
                    class_data.ParseFromString(query_data)
                    end_time = datetime.utcnow()
                    data = self._class_to_dict(device_id, class_data)
                else:
                    self.log.debug('query-no-class', device_id=device_id, class_id=class_id)
                    data = dict()
            else:
                # Get all attributes of a specific ME
                class_data = MibClassData()
                instance_data = None
                class_path = self._get_class_path(device_id, class_id)
                query_data = self._kv_store.get(class_path)
                if query_data is not None:
                    class_data.ParseFromString(query_data)
                    end_time = datetime.utcnow()

                    for inst in class_data.instances:
                        if inst.instance_id == instance_id:
                            instance_data = inst

                    if instance_data is not None:
                        if attributes is None:
                            # All Attributes
                            data = self._instance_to_dict(device_id, class_id, instance_data)

                        else:
                            # Specific attribute(s)
                            if isinstance(attributes, six.string_types):
                                attributes = {attributes}

                            data = {
                                attr.name: self._string_to_attribute(device_id,
                                                                     class_id,
                                                                     attr.name,
                                                                     attr.value)
                                for attr in instance_data.attributes if attr.name in attributes}
                    else:
                        self.log.debug('query-no-instance', device_id=device_id, class_id=class_id, entity_id=instance_id)
                        data = dict()

                else:
                    self.log.debug('query-no-class', device_id=device_id, class_id=class_id)
                    data = dict()

            return data

        except Exception as e:
            self.log.exception('query-exception', device_id=device_id, e=e)
            raise

        finally:
            if end_time is not None:
                diff = end_time.utcnow() - start_time
                # NOTE: Change to 'debug' when checked in, manually change to 'info'
                #       for development testing.
                self.log.debug('db-get-time', milliseconds=diff.microseconds / 1000, class_id=class_id,
                               entity_id=instance_id)
                self._statistics['get'].increment(diff.microseconds / 1000)

    def on_mib_reset(self, device_id):
        """
        Reset/clear the database for a specific Device

        :param device_id: (str) ONU Device ID
        :raises DatabaseStateError: If the database is not enabled
        :raises KeyError: If the device does not exist in the database
        """
        self.log.debug('on-mib-reset', device_id=device_id)

        data = MibDeviceData()

        try:
            path = self._get_device_path(device_id)
            query_data = self._kv_store.get(path)
            if query_data is not None:
                data.ParseFromString(query_data)

                # data = MibDeviceData(Wipe out any existing class IDs
                class_ids = [c.class_id for c in data.classes]

                if len(class_ids):
                    for class_id in class_ids:
                        class_path = self._get_class_path(device_id, class_id)
                        # Delete detailed classes and instances
                        self._kv_store.delete(class_path)

                # Reset MIB Data Sync to zero
                now = datetime.utcnow()
                new_data = MibDeviceData(device_id=device_id,
                                         created=data.created,
                                         last_sync_time=data.last_sync_time,
                                         mib_data_sync=0,
                                         version=MibDbExternal.CURRENT_VERSION)

                # Update with blanked out device object
                self._kv_store.set(path, new_data.SerializeToString())
                self._modified = now
                self.log.debug('mib-reset-complete', device_id=device_id)
            else:
                self.log.warn("mib-reset-no-data-to-reset", device_id=device_id)

        except Exception as e:
            self.log.exception('mib-reset-exception', device_id=device_id, e=e)
            raise

    def save_mib_data_sync(self, device_id, value):
        """
        Save the MIB Data Sync to the database in an easy location to access

        :param device_id: (str) ONU Device ID
        :param value: (int) Value to save
        """
        self.log.debug('save-mds', device_id=device_id, value=value)

        try:
            if not isinstance(value, int):
                raise TypeError('MIB Data Sync is an integer')

            if not 0 <= value <= 255:
                raise ValueError('Invalid MIB-data-sync value {}.  Must be 0..255'.
                                 format(value))
            data = MibDeviceData()
            path = self._get_device_path(device_id)
            query_data = self._kv_store.get(path)
            data.ParseFromString(query_data)

            now = datetime.utcnow()
            data.mib_data_sync = value

            # Update
            self._kv_store.set(path,data.SerializeToString())
            self._modified = now
            self.log.debug('save-mds-complete', device_id=device_id)

        except Exception as e:
            self.log.exception('save-mds-exception', device_id=device_id, e=e)
            raise

    def get_mib_data_sync(self, device_id):
        """
        Get the MIB Data Sync value last saved to the database for a device

        :param device_id: (str) ONU Device ID
        :return: (int) The Value or None if not found
        """
        self.log.debug('get-mds', device_id=device_id)

        try:
            data = MibDeviceData()
            path = self._get_device_path(device_id)
            query_data = self._kv_store.get(path)
            if query_data is not None:
                data.ParseFromString(query_data)
                return int(data.mib_data_sync)
            else:
                self.log.warn("mib-mds-no-data", device_id=device_id)
                return None  # OMCI MIB_DB entry has not yet been created

        except Exception as e:
            self.log.exception('get-mds-exception', device_id=device_id, e=e)
            raise

    def save_last_sync(self, device_id, value):
        """
        Save the Last Sync time to the database in an easy location to access

        :param device_id: (str) ONU Device ID
        :param value: (DateTime) Value to save
        """
        self.log.debug('save-last-sync', device_id=device_id, time=str(value))

        try:
            if not isinstance(value, datetime):
                raise TypeError('Expected a datetime object, got {}'.
                                format(type(datetime)))
            data = MibDeviceData()
            path = self._get_device_path(device_id)
            query_data = self._kv_store.get(path)
            data.ParseFromString(query_data)

            now = datetime.utcnow()
            data.last_sync_time = self._time_to_string(value)

            # Update
            self._kv_store.set(path, data.SerializeToString())
            self._modified = now
            self.log.debug('save-mds-complete', device_id=device_id)

        except Exception as e:
            self.log.exception('save-last-sync-exception', device_id=device_id, e=e)
            raise

    def get_last_sync(self, device_id):
        """
        Get the Last Sync Time saved to the database for a device

        :param device_id: (str) ONU Device ID
        :return: (int) The Value or None if not found
        """
        self.log.debug('get-last-sync', device_id=device_id)

        try:
            data = MibDeviceData()
            path = self._get_device_path(device_id)
            query_data = self._kv_store.get(path)
            if query_data is not None:
                data.ParseFromString(query_data)
                return self._string_to_time(data.last_sync_time)
            else:
                self.log.warn("mib-last-sync-no-data", device_id=device_id)
                return None  # OMCI MIB_DB entry has not yet been created

        except Exception as e:
            self.log.exception('get-last-sync-exception', e=e)
            raise

    def update_supported_managed_entities(self, device_id, managed_entities):
        """
        Update the supported OMCI Managed Entities for this device
        :param device_id: (str) ONU Device ID
        :param managed_entities: (set) Managed Entity class IDs
        """
        try:
            me_list = [ManagedEntity(class_id=class_id,
                                     name=self._managed_entity_to_name(device_id,
                                                                       class_id))
                       for class_id in managed_entities]
            data = MibDeviceData()
            device_path = self._get_device_path(device_id)
            query_data = self._kv_store.get(device_path)
            data.ParseFromString(query_data)

            now = datetime.utcnow()
            data.managed_entities.extend(me_list)

            # Update
            self._kv_store.set(device_path, data.SerializeToString())
            self._modified = now
            self.log.debug('save-me-list-complete', device_id=device_id)

        except Exception as e:
            self.log.exception('add-me-failure', e=e, me_list=managed_entities)
            raise

    def update_supported_message_types(self, device_id, msg_types):
        """
        Update the supported OMCI Managed Entities for this device
        :param device_id: (str) ONU Device ID
        :param msg_types: (set) Message Type values (ints)
        """
        try:
            now = datetime.utcnow()
            msg_type_list = [MessageType(message_type=msg_type.value)
                             for msg_type in msg_types]
            data = MibDeviceData()
            device_path = self._get_device_path(device_id)
            query_data = self._kv_store.get(device_path)
            data.ParseFromString(query_data)
            data.message_types.extend(msg_type_list)

            # Update
            self._kv_store.set(device_path, data.SerializeToString())
            self._modified = now
            self.log.debug('save-msg-types-complete', device_id=device_id)

        except Exception as e:
            self.log.exception('add-msg-types-failure', e=e, msg_types=msg_types)
            raise

    # Private Helper Functions

    def _get_device_path(self, device_id):
        return MibDbExternal.DEVICE_PATH.format(device_id)

    def _get_class_path(self, device_id, class_id):
        if not self._started:
            raise DatabaseStateError('The Database is not currently active')

        if not 0 <= class_id <= 0xFFFF:
            raise ValueError('class-id is 0..0xFFFF')

        fmt = MibDbExternal.CLASS_PATH
        return fmt.format(device_id, class_id)

    def _create_new_device(self, device_id):
        """
        Create an entry for new device object returning device proto object

        :param device_id: (str) ONU Device ID

        :returns: (MibDeviceData) The new populated device object
        """
        now = self._time_to_string(datetime.utcnow())
        device_data = MibDeviceData(device_id=device_id,
                                    created=now,
                                    last_sync_time='',
                                    mib_data_sync=0,
                                    version=MibDbExternal.CURRENT_VERSION)

        return device_data

    def _create_new_class(self, device_id, class_id, entity_id=None, attributes=None):
        """
        Create an entry for a new class optionally with its first instance returning class proto object

        :param device_id: (str) ONU Device ID
        :param class_id: (int) ME Class ID
        :param entity_id: (int) ME Entity ID
        :param attributes: (dict) Attribute dictionary

        :returns: (MibClassData) The new populated class data object
        """
        class_data = None
        if entity_id is not None:
            instance_data = self._create_new_instance(device_id, class_id, entity_id, attributes)
            class_data = MibClassData(class_id=class_id,
                                      instances=[instance_data])
        else:
            class_data = MibClassData(class_id=class_id)

        return class_data

    def _create_new_instance(self, device_id, class_id, entity_id, attributes):
        """
        Create an entry for a instance of a class and returning instance proto object

        :param device_id: (str) ONU Device ID
        :param class_id: (int) ME Class ID
        :param entity_id: (int) ME Entity ID
        :param attributes: (dict) Attribute dictionary

        :returns: (MibInstanceData) The new populated instance object
        """
        attrs = []
        for k, v in attributes.items():
            str_value = self._attribute_to_string(device_id, class_id, k, v)
            attrs.append(MibAttributeData(name=k, value=str_value))

        now = self._time_to_string(datetime.utcnow())
        instance_data = MibInstanceData(instance_id=entity_id,
                                        created=now,
                                        modified=now,
                                        attributes=attrs)

        return instance_data

    def _update_existing_instance(self, device_id, class_id, entity_id, attributes, existing_instance):
        """
        Update the attributes of an existing instance of a class and returning the modified instance proto object

        :param device_id: (str) ONU Device ID
        :param class_id: (int) ME Class ID
        :param entity_id: (int) ME Entity ID
        :param existing_instance: (MibInstanceData) current instance object
        :param attributes: (dict) Attribute dictionary

        :returns: (MibInstanceData) The updated instance object or None if nothing changed
        """
        new_attributes = []
        exist_attr_indexes = dict()
        attr_len = len(existing_instance.attributes)

        modified = False
        for index in range(0, attr_len):
            name = existing_instance.attributes[index].name
            value = existing_instance.attributes[index].value
            exist_attr_indexes[name] = index
            new_attributes.append(MibAttributeData(name=name, value=value))

        for k, v in attributes.items():
            try:
                old_value = None if k not in exist_attr_indexes \
                    else new_attributes[exist_attr_indexes[k]].value

                str_value = self._attribute_to_string(device_id, class_id, k, v, old_value)

                if k not in exist_attr_indexes:
                    new_attributes.append(MibAttributeData(name=k, value=str_value))
                    modified = True

                elif new_attributes[exist_attr_indexes[k]].value != str_value:
                    new_attributes[exist_attr_indexes[k]].value = str_value
                    modified = True

            except Exception as e:
                self.log.exception('save-error', e=e, class_id=class_id,
                                   attr=k, value_type=type(v))

        if modified:
            now = self._time_to_string(datetime.utcnow())
            new_instance_data = MibInstanceData(instance_id=entity_id,
                                                created=existing_instance.created,
                                                modified=now,
                                                attributes=new_attributes)
            return new_instance_data
        else:
            return None

    def _time_to_string(self, time):
        return time.strftime(MibDbExternal._TIME_FORMAT) if time is not None else ''

    def _string_to_time(self, time):
        return datetime.strptime(time, MibDbExternal._TIME_FORMAT) if len(time) else None

    def _attribute_to_string(self, device_id, class_id, attr_name, value, old_value=None):
        """
        Convert an ME's attribute value to string representation

        :param device_id: (str) ONU Device ID
        :param class_id: (int) Class ID
        :param attr_name: (str) Attribute Name (see EntityClasses)
        :param value: (various) Attribute Value

        :return: (str) String representation of the value
        :raises KeyError: Device, Class ID, or Attribute does not exist
        """
        try:
            me_map = self._omci_agent.get_device(device_id).me_map

            if class_id in me_map:
                entity = me_map[class_id]
                attr_index = entity.attribute_name_to_index_map[attr_name]
                eca = entity.attributes[attr_index]
                field = eca.field
            else:
                # Here for auto-defined MEs (ones not defined in ME Map)
                from pyvoltha.adapters.extensions.omci.omci_cc import UNKNOWN_CLASS_ATTRIBUTE_KEY
                field = StrFixedLenField(UNKNOWN_CLASS_ATTRIBUTE_KEY, None, 24)

            if isinstance(field, StrFixedLenField):
                from scapy.base_classes import Packet_metaclass
                if hasattr(value, 'to_json') and not isinstance(value, six.string_types):
                    # Packet Class to string
                    str_value = value.to_json()
                elif isinstance(field.default, Packet_metaclass) \
                        and hasattr(field.default, 'json_from_value'):
                    # Value/hex of Packet Class to string
                    str_value = field.default.json_from_value(value)
                else:
                    str_value = str(value)

            elif isinstance(field, OmciSerialNumberField):
                # For some reason some ONU encode quotes in the serial number...
                other_value = value.replace("'", "")
                str_value = str(other_value)

            elif isinstance(field, (StrField, MACField, IPField)):
                #  For StrField, value is an str already
                #  For MACField, value is a string in ':' delimited form
                #  For IPField, value is a string in '.' delimited form
                str_value = str(value)

            elif isinstance(field, (ByteField, ShortField, IntField, LongField)):
                #  For ByteField, ShortField, IntField, and LongField value is an int
                str_value = str(value)

            elif isinstance(field, BitField):
                # For BitField, value is a long
                #
                str_value = str(value)

            elif hasattr(field, 'to_json'):
                str_value = field.to_json(value, old_value)

            elif isinstance(field, FieldListField):
                str_value = json.dumps(value, separators=(',', ':'))

            else:
                self.log.warning('default-conversion', type=type(field),
                                 class_id=class_id, attribute=attr_name, value=str(value))
                str_value = str(value)

            return str_value

        except Exception as e:
            self.log.exception('attr-to-string', device_id=device_id,
                               class_id=class_id, attr=attr_name,
                               value=value, e=e)
            raise

    def _string_to_attribute(self, device_id, class_id, attr_name, str_value):
        """
        Convert an ME's attribute value-string to its Scapy decode equivalent

        :param device_id: (str) ONU Device ID
        :param class_id: (int) Class ID
        :param attr_name: (str) Attribute Name (see EntityClasses)
        :param str_value: (str) Attribute Value in string form

        :return: (various) String representation of the value
        :raises KeyError: Device, Class ID, or Attribute does not exist
        """
        try:
            me_map = self._omci_agent.get_device(device_id).me_map

            if class_id in me_map:
                entity = me_map[class_id]
                attr_index = entity.attribute_name_to_index_map[attr_name]
                eca = entity.attributes[attr_index]
                field = eca.field
            else:
                # Here for auto-defined MEs (ones not defined in ME Map)
                from pyvoltha.adapters.extensions.omci.omci_cc import UNKNOWN_CLASS_ATTRIBUTE_KEY
                field = StrFixedLenField(UNKNOWN_CLASS_ATTRIBUTE_KEY, None, 24)

            if isinstance(field, StrFixedLenField):
                from scapy.base_classes import Packet_metaclass
                default = field.default
                if isinstance(default, Packet_metaclass) and \
                        hasattr(default, 'to_json'):
                    value = json.loads(str_value)
                else:
                    value = str_value

            elif isinstance(field, OmciSerialNumberField):
                value = str_value

            elif isinstance(field, MACField):
                value = str_value

            elif isinstance(field, IPField):
                value = str_value

            elif isinstance(field, (ByteField, ShortField, IntField, LongField)):
                if str_value.lower() in ('true', 'false'):
                    str_value = '1' if str_value.lower() == 'true' else '0'
                value = int(str_value)

            elif isinstance(field, BitField):
                value = int(str_value)

            elif hasattr(field, 'load_json'):
                value = field.load_json(str_value)

            elif isinstance(field, FieldListField):
                value = json.loads(str_value)

            else:
                self.log.warning('default-conversion', type=type(field),
                                 class_id=class_id, attribute=attr_name, value=str_value)
                value = None

            return value

        except Exception as e:
            self.log.exception('attr-to-string', device_id=device_id,
                               class_id=class_id, attr=attr_name,
                               value=str_value, e=e)
            raise

    def _instance_to_dict(self, device_id, class_id, instance):
        if not isinstance(instance, MibInstanceData):
            raise TypeError('{} is not of type MibInstanceData'.format(type(instance)))

        data = {
            INSTANCE_ID_KEY: instance.instance_id,
            CREATED_KEY: self._string_to_time(instance.created),
            MODIFIED_KEY: self._string_to_time(instance.modified),
            ATTRIBUTES_KEY: dict()
        }
        for attribute in instance.attributes:
            data[ATTRIBUTES_KEY][attribute.name] = self._string_to_attribute(device_id,
                                                                             class_id,
                                                                             attribute.name,
                                                                             attribute.value)
        return data

    def _class_to_dict(self, device_id, val):
        if not isinstance(val, MibClassData):
            raise TypeError('{} is not of type MibClassData'.format(type(val)))

        data = {
            CLASS_ID_KEY: val.class_id
        }
        for instance in val.instances:
            data[instance.instance_id] = self._instance_to_dict(device_id,
                                                                val.class_id,
                                                                instance)
        return data

    def _device_to_dict(self, val, classes_dict=None):
        if not isinstance(val, MibDeviceData):
            raise TypeError('{} is not of type MibDeviceData'.format(type(val)))

        data = {
            DEVICE_ID_KEY: val.device_id,
            CREATED_KEY: self._string_to_time(val.created),
            LAST_SYNC_KEY: self._string_to_time(val.last_sync_time),
            MDS_KEY: val.mib_data_sync,
            VERSION_KEY: val.version,
            ME_KEY: dict(),
            MSG_TYPE_KEY: set()
        }
        if classes_dict is None:
            for class_data in val.classes:
                data[class_data.class_id] = self._class_to_dict(val.device_id,
                                                                class_data)
        else:
            data.update(classes_dict)

        for managed_entity in val.managed_entities:
            data[ME_KEY][managed_entity.class_id] = managed_entity.name

        for msg_type in val.message_types:
            data[MSG_TYPE_KEY].add(msg_type.message_type)

        return data

    def _managed_entity_to_name(self, device_id, class_id):
        me_map = self._omci_agent.get_device(device_id).me_map
        entity = me_map.get(class_id)

        return entity.__name__ if entity is not None else 'UnknownManagedEntity'

    def load_from_template(self, device_id, template):
        now = datetime.utcnow()
        headerdata = {
            DEVICE_ID_KEY: device_id,
            CREATED_KEY: now,
            LAST_SYNC_KEY: None,
            MDS_KEY: 0,
            VERSION_KEY: MibDbExternal.CURRENT_VERSION,
            ME_KEY: dict(),
            MSG_TYPE_KEY: set()
        }
        template.update(headerdata)

        for cls_id, cls_data in template.items():
            if isinstance(cls_id, int):
                for inst_id, inst_data in cls_data.items():
                    if isinstance(inst_id, int):
                        self.set(device_id, cls_id, inst_id, template[cls_id][inst_id][ATTRIBUTES_KEY])

    def dump_to_json(self, device_id):
        device_db = self.query(device_id)
        def json_converter(o):
            if isinstance(o, datetime):
                return o.__str__()
            if isinstance(o, six.binary_type):
                return o.decode('ascii')

        json_string = json.dumps(device_db, default=json_converter, indent=2)

        return json_string
