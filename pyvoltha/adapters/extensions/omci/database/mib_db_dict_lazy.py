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
import json
from twisted.internet.task import LoopingCall
from twisted.internet.defer import inlineCallbacks, returnValue
from .mib_db_api import *
from .mib_db_dict import MibDbVolatileDict
from pyvoltha.adapters.common.kvstore.twisted_etcd_store import TwistedEtcdStore
from pyvoltha.common.utils.registry import registry

LAST_LAZY_WRITE_KEY = 'last_lazy_write'
DIRTY_DB_KEY = 'dirty_db'
LAZY_DEFERRED_KEY = 'lazy_deferred'
PENDING_DELETE = 'pending_delete'
CHECK_INTERVAL = 60


class MibDbLazyWriteDict(MibDbVolatileDict):

    # Paths from kv store
    MIB_PATH = 'service/voltha/omci_mibs'
    DEVICE_PATH = '{}'  # .format(device_id)

    def __init__(self, omci_agent):
        super(MibDbLazyWriteDict, self).__init__(omci_agent)

        self.args = registry('main').get_args()
        host, port = self.args.etcd.split(':', 1)
        self._kv_store = TwistedEtcdStore(host, port, MibDbLazyWriteDict.MIB_PATH)
        self._lazymetadata = dict()

    @inlineCallbacks
    def add(self, device_id, overwrite=False):

        existing_db = yield self._load_device_data(device_id)
        if existing_db:
            # populate device database if exists in etcd
            self._data[device_id] = existing_db
            now = datetime.utcnow()
            self._lazymetadata[device_id] = {
                LAST_LAZY_WRITE_KEY: now,
                DIRTY_DB_KEY: False,
                PENDING_DELETE: False
            }
            self.log.debug('recovered-device-from-storage', device_id=device_id, metadata=self._lazymetadata[device_id])
        else:
            # new device with no persistent storage.
            self._lazymetadata[device_id] = {
                LAST_LAZY_WRITE_KEY: None,
                DIRTY_DB_KEY: True,
                PENDING_DELETE: False
            }
            self.log.debug('add-device-for-lazy-sync', device_id=device_id, metadata=self._lazymetadata[device_id])

        self._lazymetadata[device_id][LAZY_DEFERRED_KEY] = LoopingCall(self._check_dirty, device_id)
        self._lazymetadata[device_id][LAZY_DEFERRED_KEY].start(CHECK_INTERVAL, now=False)

        super(MibDbLazyWriteDict, self).add(device_id, overwrite)

    def remove(self, device_id):
        super(MibDbLazyWriteDict, self).remove(device_id)
        self._lazymetadata[device_id][DIRTY_DB_KEY] = True
        self._lazymetadata[device_id][PENDING_DELETE] = True
        self.log.debug('setting-sync-remove-flag', device_id=device_id, metadata=self._lazymetadata[device_id])

    def on_mib_reset(self, device_id):
        super(MibDbLazyWriteDict, self).on_mib_reset(device_id)
        self._lazymetadata[device_id][DIRTY_DB_KEY] = True

    def save_mib_data_sync(self, device_id, value):
        results = super(MibDbLazyWriteDict, self).save_mib_data_sync(device_id, value)
        self._lazymetadata[device_id][DIRTY_DB_KEY] = True
        return results

    def _check_dirty(self, device_id):
        if self._lazymetadata[device_id][DIRTY_DB_KEY] is True:
            self.log.debug('dirty-cache-writing-data', device_id=device_id, metadata=self._lazymetadata[device_id])
            self._sync(device_id)
        else:
            self.log.debug('clean-cache-checking-later', device_id=device_id, metadata=self._lazymetadata[device_id])

    @inlineCallbacks
    def _sync(self, device_id):
        json = super(MibDbLazyWriteDict, self).dump_to_json(device_id)
        now = datetime.utcnow()
        device_path = self._get_device_path(device_id)

        if self._lazymetadata[device_id][PENDING_DELETE] is True:
            yield self._kv_store.delete(device_path)
            self.log.debug('removed-synced-data', device_id=device_id, metadata=self._lazymetadata[device_id])
            d = self._lazymetadata[device_id][LAZY_DEFERRED_KEY]
            del self._lazymetadata[device_id]
            d.stop()
        else:
            yield self._kv_store.set(device_path, json)
            self._lazymetadata[device_id][LAST_LAZY_WRITE_KEY] = now
            self._lazymetadata[device_id][DIRTY_DB_KEY] = False
            self.log.debug('synced-data', device_id=device_id, metadata=self._lazymetadata[device_id])

    @inlineCallbacks
    def _load_device_data(self, device_id):
        device_path = self._get_device_path(device_id)
        json = yield self._kv_store.get(device_path)
        if json:
            lookupdb = self._load_from_json(json)
            self.log.debug('looked-up-device', device_path=device_path)
            returnValue(lookupdb)
        else:
            returnValue(None)

    def _load_from_json(self, jsondata):

        def json_obj_parser(x):
            if isinstance(x, dict):
                results = dict()
                for (key, value) in x.items():
                    try:
                        key = int(key)
                    except (ValueError, TypeError):
                        pass

                    results.update({key: value})
                return results
            return x

        device_data = json.loads(jsondata, object_hook=json_obj_parser)
        return device_data

    def _get_device_path(self, device_id):
        return MibDbLazyWriteDict.DEVICE_PATH.format(device_id)
