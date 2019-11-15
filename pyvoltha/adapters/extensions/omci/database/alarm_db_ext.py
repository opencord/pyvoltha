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
from __future__ import absolute_import
from .mib_db_api import *
from voltha_protos.omci_alarm_db_pb2 import AlarmInstanceData, AlarmClassData, \
    AlarmDeviceData, AlarmAttributeData
from pyvoltha.common.config.config_backend import EtcdStore
from pyvoltha.common.utils.registry import registry
import six
from six.moves import range

class AlarmDbExternal(MibDbApi):
    """
    A persistent external OpenOMCI Alarm Database
    """
    CURRENT_VERSION = 1                       # VOLTHA v1.3.0 release
    ALARM_BITMAP_KEY = 'alarm_bit_map'

    _TIME_FORMAT = '%Y%m%d-%H%M%S.%f'

    # Paths from root proxy
    ALARM_PATH = '/omci_alarms'
    DEVICE_PATH = '{}'            # .format(device_id)

    # Classes, Instances, and Attributes as lists from root proxy
    CLASS_PATH = DEVICE_PATH + '/classes/{}'                                # .format(device_id, class_id)
    INSTANCE_PATH = DEVICE_PATH + '/classes/{}/instances/{}'                 # .format(device_id, class_id, instance_id)

    def __init__(self, omci_agent):
        """
        Class initializer
        :param omci_agent: (OpenOMCIAgent) OpenOMCI Agent
        """
        super(AlarmDbExternal, self).__init__(omci_agent)

        self.args = registry('main').get_args()
        host, port = self.args.etcd.split(':', 1)
        self._kv_store = EtcdStore(host, port, AlarmDbExternal.ALARM_PATH)

    def start(self):
        """
        Start up/restore the database
        """
        self.log.debug('start')

        if not self._started:
            super(AlarmDbExternal, self).start()

    def stop(self):
        """
        Start up the database
        """
        self.log.debug('stop')

        if self._started:
            super(AlarmDbExternal, self).stop()
            # TODO: Delete this method if nothing else is done except calling the base class

    def _time_to_string(self, time):
        return time.strftime(AlarmDbExternal._TIME_FORMAT) if time is not None else ''

    def _string_to_time(self, time):
        return datetime.strptime(time, AlarmDbExternal._TIME_FORMAT) if len(time) else None

    def _attribute_to_string(self, value):
        """
        Convert an ME's attribute value to string representation

        :param value: (long) Alarm bitmaps are always a Long
        :return: (str) String representation of the value
        """
        return str(value)

    def _string_to_attribute(self, str_value):
        """
        Convert an ME's attribute value-string to its Scapy decode equivalent

        :param device_id: (str) ONU Device ID
        :param class_id: (int) Class ID
        :param attr_name: (str) Attribute Name (see EntityClasses)
        :param str_value: (str) Attribute Value in string form

        :return: (various) String representation of the value
        :raises KeyError: Device, Class ID, or Attribute does not exist
        """
        # Alarms are always a bitmap which is a long
        return int(str_value) if len(str_value) else 0

    def add(self, device_id, overwrite=False):
        """
        Add a new ONU to database

        :param device_id: (str) Device ID of ONU to add
        :param overwrite: (bool) Overwrite existing entry if found.

        :raises KeyError: If device already exists and 'overwrite' is False
        """
        self.log.debug('add-device', device_id=device_id, overwrite=overwrite)

        now = datetime.utcnow()
        found = False

        data = AlarmDeviceData(device_id=device_id,
                               created=self._time_to_string(now),
                               version=AlarmDbExternal.CURRENT_VERSION,
                               last_alarm_sequence=0)
        path = self._get_device_path(device_id)
        self.log.debug("add-device-path", device_id=device_id, path=path)
        try:
            #raises KeyError if not found
            device = self._kv_store[path]

            #device is found at this point
            found = True

            if not overwrite:
                # Device already exists
                raise KeyError('Device with ID {} already exists in Alarm database'.
                               format(device_id))

            # Overwrite with new data
            self._kv_store[path] = data.SerializeToString()
            self._modified = now

        except KeyError:
            if found:
                raise
            # Did not exist, add it now
            self._kv_store[path] = data.SerializeToString()
            self._created = now
            self._modified = now

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
            del self._kv_store[path]
            self._modified = datetime.utcnow()

        except KeyError:
            # Did not exists, which is not a failure
            pass

        except Exception as e:
            self.log.exception('remove-exception', device_id=device_id, e=e)
            raise

    def _get_device_path(self, device_id):
        return AlarmDbExternal.DEVICE_PATH.format(device_id)

    def _get_class_path(self, device_id, class_id):
        if not self._started:
            raise DatabaseStateError('The Database is not currently active')

        if not 0 <= class_id <= 0xFFFF:
            raise ValueError('class-id is 0..0xFFFF')

        fmt = AlarmDbExternal.CLASS_PATH
        return fmt.format(device_id, class_id)


    def _get_instance_path(self, device_id, class_id, instance_id):
        if not self._started:
            raise DatabaseStateError('The Database is not currently active')

        if not isinstance(device_id, six.string_types):
            raise TypeError('Device ID is a string')

        if not 0 <= class_id <= 0xFFFF:
            raise ValueError('class-id is 0..0xFFFF')

        if not 0 <= instance_id <= 0xFFFF:
            raise ValueError('instance-id is 0..0xFFFF')

        fmt = AlarmDbExternal.INSTANCE_PATH
        return fmt.format(device_id, class_id, instance_id)

    def save_last_sync_time(self, device_id, value):
        """
        Save the Last Sync time to the database in an easy location to access

        :param device_id: (str) ONU Device ID
        :param value: (DateTime) Value to save
        """
        self.log.debug('save-last-sync-time', device_id=device_id, time=str(value))

        try:
            if not isinstance(value, datetime):
                raise TypeError('Expected a datetime object, got {}'.
                                format(type(datetime)))

            data = AlarmDeviceData()
            path = self._get_device_path(device_id)
            data.ParseFromString(self._kv_store[path])

            now = datetime.utcnow()
            data.last_sync_time = self._time_to_string(value)

            # Update
            self._kv_store[path] = data.SerializeToString()
            self._modified = now
            self.log.debug('save-sync-time-complete', device_id=device_id)

        except Exception as e:
            self.log.exception('save-last-sync-exception', device_id=device_id, e=e)
            raise

    def get_last_sync_time(self, device_id):
        """
        Get the Last Sync Time saved to the database for a device

        :param device_id: (str) ONU Device ID
        :return: (int) The Value or None if not found
        """
        self.log.debug('get-last-sync-time', device_id=device_id)

        try:
            data = AlarmDeviceData()
            path = self._get_device_path(device_id)
            data.ParseFromString(self._kv_store[path])
            return self._string_to_time(data.last_sync_time)

        except KeyError:
            return None     # OMCI MIB_DB entry has not yet been created

        except Exception as e:
            self.log.exception('get-last-sync-time-exception', e=e)
            raise

    def save_alarm_last_sync(self, device_id, value):
        """
        Save the Last Alarm Sequence value to the database in an easy location to access

        :param device_id: (str) ONU Device ID
        :param value: (int) Value to save
        """
        self.log.debug('save-last-sync', device_id=device_id, seq=str(value))

        try:
            if not isinstance(value, int):
                raise TypeError('Expected a integer, got {}'.format(type(value)))

            data = AlarmDeviceData()
            path = self._get_device_path(device_id)
            data.ParseFromString(self._kv_store[path])

            now = datetime.utcnow()
            data.last_alarm_sequence = int(value)

            # Update
            self._kv_store[path] = data.SerializeToString()
            self._modified = now
            self.log.debug('save-sequence-complete', device_id=device_id)

        except Exception as e:
            self.log.exception('save-last-sync-exception', device_id=device_id, e=e)
            raise

    def get_alarm_last_sync(self, device_id):
        """
        Get the Last Sync Time saved to the database for a device

        :param device_id: (str) ONU Device ID
        :return: (int) The Value or None if not found
        """
        self.log.debug('get-last-sync', device_id=device_id)

        try:
            data = AlarmDeviceData()
            path = self._get_device_path(device_id)
            data.ParseFromString(self.kv_store[path])
            return int(data.last_alarm_sequence)

        except KeyError:
            return None     # OMCI ALARM_DB entry has not yet been created

        except Exception as e:
            self.log.exception('get-last-alarm-exception', e=e)
            raise

    def _add_new_class_and_instance(self, device_id, class_id, instance_id, attributes):
        """
        Create an entry for a new class in the external database

        :param device_id: (str) ONU Device ID
        :param class_id: (int) ME Class ID
        :param instance_id: (int) ME Entity ID
        :param attributes: (dict) Attribute dictionary

        :returns: (bool) True if the value was saved to the database. False if the
                         value was identical to the current instance
        """
        self.log.debug('add-new-class-and-instance', device_id=device_id, class_id=class_id,
                       instance_id=instance_id, attributes=attributes)

        class_data = AlarmClassData(class_id=class_id)

        class_path = AlarmDbExternal.CLASS_PATH.format(device_id, class_id)
        self._kv_store[class_path] = class_data.SerializeToString()

        inst_data = self._create_new_instance(device_id, class_id, instance_id, attributes)
        inst_path = AlarmDbExternal.INSTANCE_PATH.format(device_id, class_id, instance_id)
        self._kv_store[inst_path] = inst_data.SerializeToString()

        self.log.debug('set-complete', device_id=device_id, class_id=class_id,
                       entity_id=instance_id, attributes=attributes)
        return True

    def _create_new_instance(self,  device_id, class_id, instance_id, attributes):
        """
        Create an entry for a instance of an existing class in the external database

        :param device_id: (str) ONU Device ID
        :param class_id: (int) ME Class ID
        :param instance_id: (int) ME Entity ID
        :param attributes: (dict) Attribute dictionary

        :returns: (AlarmInstanceData) The new instance object
        """
        self.log.debug('create-new-instance', device_id=device_id, class_id=class_id,
                       instance_id=instance_id, attributes=attributes)

        now = self._time_to_string(datetime.utcnow())
        attrs = [AlarmAttributeData(name=k,
                                    value=self._attribute_to_string(v)) for k, v in attributes.items()]
        instance_data = AlarmInstanceData(instance_id=instance_id,
                                          created=now,
                                          modified=now,
                                          attributes=attrs)

        self.log.debug('create-new-instance-complete', device_id=device_id, class_id=class_id,
                       entity_id=instance_id, attributes=attributes)
        return instance_data

    def set(self, device_id, class_id, instance_id, attributes):
        """
        Set a database value.  This should only be called by the Alarm synchronizer
        and its related tasks

        :param device_id: (str) ONU Device ID
        :param class_id: (int) ME Class ID
        :param instance_id: (int) ME Entity ID
        :param attributes: (dict) Attribute dictionary

        :returns: (bool) True if the value was saved to the database. False if the
                         value was identical to the current instance

        :raises KeyError: If device does not exist
        :raises DatabaseStateError: If the database is not enabled
        """
        self.log.debug('set', device_id=device_id, class_id=class_id,
                       instance_id=instance_id, attributes=attributes)
        try:
            if not isinstance(device_id, six.string_types):
                raise TypeError('Device ID should be a string')

            if not 0 <= class_id <= 0xFFFF:
                raise ValueError("Invalid Class ID: {}, should be 0..65535".format(class_id))

            if not 0 <= instance_id <= 0xFFFF:
                raise ValueError("Invalid Instance ID: {}, should be 0..65535".format(instance_id))

            if not isinstance(attributes, dict):
                raise TypeError("Attributes should be a dictionary")

            if not self._started:
                raise DatabaseStateError('The Database is not currently active')

            try:
                class_data = AlarmClassData()
                class_path = AlarmDbExternal.CLASS_PATH.format(device_id, class_id)
                class_data.ParseFromString(self._kv_store[class_path])

                modified = False
                new_data = None
                try:
                    inst_data = AlarmInstanceData()
                    inst_path = AlarmDbExternal.INSTANCE_PATH.format(device_id, class_id, instance_id)
                    inst_data.ParseFromString(self._kv_store[inst_path])

                    exist_attr_indexes = dict()
                    attr_len = len(inst_data.attributes)

                    for index in range(0, attr_len):
                        exist_attr_indexes[inst_data.attributes[index].name] = index

                    str_value = ''
                    new_attributes = []

                    for k, v in attributes.items():
                        try:
                            str_value = self._attribute_to_string(v)
                            new_attributes.append(AlarmAttributeData(name=k, value=str_value))

                        except Exception as e:
                            self.log.exception('save-error', e=e, class_id=class_id,
                                            attr=k, value_type=type(v))

                        if k not in exist_attr_indexes or \
                                inst_data.attributes[exist_attr_indexes[k]].value != str_value:
                            modified = True
                            self.log.debug('different-attributes', device_id=device_id, class_id=class_id,
                                    instance_id=instance_id, attributes=inst_data.attributes, new_attributes=new_attributes)

                    if modified:
                        now = datetime.utcnow()
                        new_data = AlarmInstanceData(instance_id=instance_id,
                                                    created=inst_data.created,
                                                    modified=self._time_to_string(now),
                                                    attributes=new_attributes)

                except KeyError:
                    # Here if the instance_id does not yet exist in the database
                    new_data = self._create_new_instance(device_id, class_id, instance_id, attributes)
                    modified = True

                if modified:
                    del self._kv_store[inst_path]
                    self._kv_store[inst_path] = new_data.SerializeToString()
                return modified

            except KeyError:
                # Here if the class-id does not yet exist in the database
                return self._add_new_class_and_instance(device_id, class_id, instance_id,
                                           attributes)
        except Exception as e:
            self.log.exception('set-exception', device_id=device_id, class_id=class_id,
                               instance_id=instance_id, attributes=attributes, e=e)
            raise

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

        try:
            instpath = self._get_instance_path(device_id, class_id, entity_id)
            del self._kv_store[instpath]

            self._modified = datetime.utcnow()
            return True

        except KeyError:
            return False    # Not found

        except Exception as e:
            self.log.exception('get-last-data-exception', device_id=device_id, e=e)
            raise

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
                       entity_instance_id=instance_id, attributes=attributes)
        data = dict()

        try:
            if class_id is None:
                # Get full device info
                self.log.warn('get-all-instances-by-device-not-supported')
                try:
                    dev_data = AlarmDeviceData()
                    device_path = self._get_device_path(device_id)
                    dev_data.ParseFromString(self._kv_store[device_path])
                    data = self._device_to_dict(dev_data)

                except KeyError:
                    data = dict()

            elif instance_id is None:
                # Get all instances of the class
                self.log.warn('get-all-instances-by-class-not-supported')
                try:
                    cls_data = AlarmClassData()
                    class_path = self._get_class_path(device_id, class_id)
                    cls_data.ParseFromString(self._kv_store[class_path])
                    data = self._class_to_dict(cls_data)

                except KeyError:
                    data = dict()

            else:
                # Get all attributes of a specific ME
                try:
                    inst_data = AlarmInstanceData()
                    inst_path = self._get_instance_path(device_id, class_id, instance_id)
                    inst_data.ParseFromString(self._kv_store[inst_path])

                    if attributes is None:
                        # All Attributes
                        data = self._instance_to_dict(inst_data)
                        self.log.debug('query-result-all', data=data)
                    else:
                        # Specific attribute(s)
                        if isinstance(attributes, six.string_types):
                            attributes = {attributes}

                        data = {
                            attr.name: self._string_to_attribute(attr.value)
                            for attr in inst_data.attributes if attr.name in attributes}

                except KeyError:
                    self.log.debug('no-instance-data-keyError')
                    data = dict()

                except Exception as e:
                    self.log.exception('get-last-sync-exception', device_id=device_id, e=e)
                    raise

            self.log.debug('query-result', data=data)
            return data

        except KeyError:
            self.log.warn('query-no-device', device_id=device_id)
            raise

        except Exception as e:
            self.log.exception('get-last-sync-exception', device_id=device_id, e=e)
            raise

    def _instance_to_dict(self, instance):
        if not isinstance(instance, AlarmInstanceData):
            raise TypeError('{} is not of type AlarmInstanceData'.format(type(instance)))

        data = {
            INSTANCE_ID_KEY: instance.instance_id,
            CREATED_KEY: self._string_to_time(instance.created),
            MODIFIED_KEY: self._string_to_time(instance.modified),
            ATTRIBUTES_KEY: dict()
        }
        for attribute in instance.attributes:
            data[ATTRIBUTES_KEY][attribute.name] = self._string_to_attribute(attribute.value)
        return data

    def _class_to_dict(self, val):
        if not isinstance(val, AlarmClassData):
            raise TypeError('{} is not of type AlarmClassData'.format(type(val)))

        data = {
            CLASS_ID_KEY: val.class_id,
        }
        for instance in val.instances:
            data[instance.instance_id] = self._instance_to_dict(instance)
        return data

    def _device_to_dict(self, val):
        if not isinstance(val, AlarmDeviceData):
            raise TypeError('{} is not of type AlarmDeviceData'.format(type(val)))

        data = {
            DEVICE_ID_KEY: val.device_id,
            CREATED_KEY: self._string_to_time(val.created),
            VERSION_KEY: val.version,
            ME_KEY: dict(),
            MSG_TYPE_KEY: set()
        }
        for class_data in val.classes:
            data[class_data.class_id] = self._class_to_dict(class_data)
        for managed_entity in val.managed_entities:
            data[ME_KEY][managed_entity.class_id] = managed_entity.name

        for msg_type in val.message_types:
            data[MSG_TYPE_KEY].add(msg_type.message_type)

        return data
