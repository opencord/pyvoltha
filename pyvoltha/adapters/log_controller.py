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
import os
import structlog
from pyvoltha.adapters.common.kvstore.twisted_etcd_store import TwistedEtcdStore
from pyvoltha.common.structlog_setup import setup_logging, update_logging, validate_loglevel, string_to_int
from twisted.internet.defer import inlineCallbacks, returnValue


COMPONENT_NAME = os.environ.get("COMPONENT_NAME")
GLOBAL_CONFIG_ROOT_NODE = "global"
DEFAULT_KV_STORE_CONFIG_PATH = "config"
KV_STORE_DATA_PATH_PREFIX = "service/voltha"
KV_STORE_PATH_SEPARATOR = "/"
CONFIG_TYPE = "loglevel"
DEFAULT_PACKAGE_NAME = "default"
GLOBAL_DEFAULT_LOGLEVEL = "WARN"

class LogController():
    instance_id = None
    etcd_client = None
    active_log_hash = None


    def __init__(self, etcd_host, etcd_port):
        self.log = structlog.get_logger()
        self.etcd_host = etcd_host
        self.etcd_port = etcd_port


    def create_kv_client(self):
        client = TwistedEtcdStore(self.etcd_host, self.etcd_port, KV_STORE_DATA_PATH_PREFIX)
        LogController.etcd_client = client
        return client


    def make_config_path(self, key):
        return (DEFAULT_KV_STORE_CONFIG_PATH + KV_STORE_PATH_SEPARATOR + key + KV_STORE_PATH_SEPARATOR + CONFIG_TYPE + KV_STORE_PATH_SEPARATOR + DEFAULT_PACKAGE_NAME)

    @inlineCallbacks
    def get_global_loglevel(self):

        global_default_loglevel = ""
        global_config_path = self.make_config_path(GLOBAL_CONFIG_ROOT_NODE)

        try:
            self.log_level = yield LogController.etcd_client.get(global_config_path)
            level = validate_loglevel(str(self.log_level, 'utf-8'))

            if level == "":
                self.log.warn("Unsupported loglevel at global config path", level)
            else:
                global_default_loglevel = level

        except KeyError:
            self.log.warn("Failed to retrive default global loglevel")

        self.log.debug("Retrieved global default loglevel")
        result = yield global_default_loglevel
        returnValue(result)


    @inlineCallbacks
    def get_component_loglevel(self, global_default_loglevel):

        component_default_loglevel = global_default_loglevel
        component_config_path = self.make_config_path(COMPONENT_NAME)

        try:
            self.log_level = yield LogController.etcd_client.get(component_config_path)
            if self.log_level is not None:
                level = validate_loglevel(str(self.log_level, 'utf-8'))

                if level == "":
                    self.log.warn("Unsupported loglevel at component config path", level)
                else:
                    component_default_loglevel = level

        except KeyError:
            self.log.warn("Failed to retrive default component loglevel")
            component_default_loglevel = global_default_loglevel

        self.log.debug("Retrieved component default loglevel", component_default_loglevel)
        result = yield component_default_loglevel
        returnValue(result)


    @inlineCallbacks
    def start_watch_log_config_change(self, instance_id, initial_default_loglevel):

        self.log.debug("Start watching for log config change")
        LogController.instance_id = instance_id

        if COMPONENT_NAME == None:
            raise Exception("Unable to retrive pod component name from runtime-env")

        self.client = self.create_kv_client()

        self.global_config_path = self.make_config_path(GLOBAL_CONFIG_ROOT_NODE)
        self.component_config_path = self.make_config_path(COMPONENT_NAME)   

        yield self.set_default_loglevel(self.global_config_path, self.component_config_path, initial_default_loglevel.upper())
        yield self.process_log_config_change()

        yield self.client.watch(self.global_config_path, self.watch_callback)
        yield self.client.watch(self.component_config_path, self.watch_callback)


    @inlineCallbacks
    def watch_callback(self, event):
        yield self.process_log_config_change()


    @inlineCallbacks
    def process_log_config_change(self):
        self.log.debug("processing log config change")

        self.global_default_level = yield self.get_global_loglevel()
        level = yield self.get_component_loglevel(self.global_default_level)
        try:
            self.loglevel = string_to_int(level)
        except ValueError:
            self.log.warn('Invalid loglevel is given : ', level)

        current_log_hash = hash(self.loglevel)
        if LogController.active_log_hash != current_log_hash:
            LogController.active_log_hash = current_log_hash
            self.log.debug("applying updated loglevel")
            update_logging(LogController.instance_id, None, verbosity_adjust=self.loglevel)


    @inlineCallbacks
    def set_default_loglevel(self, global_config_path, component_config_path, initial_default_loglevel):

        if (yield LogController.etcd_client.get(global_config_path)) == None:
            yield LogController.etcd_client.set(global_config_path, GLOBAL_DEFAULT_LOGLEVEL)

        if (yield LogController.etcd_client.get(component_config_path)) == None:
            yield LogController.etcd_client.set(component_config_path, initial_default_loglevel)
