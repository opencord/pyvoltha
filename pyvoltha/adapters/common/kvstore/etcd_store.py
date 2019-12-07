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

import etcd3


class EtcdStore(object):

    def __init__(self, host, port, path_prefix):
        self._etcd = etcd3.client(host=host, port=port)
        self.host = host
        self.port = port
        self._path_prefix = path_prefix

    def make_path(self, key):
        return '{}/{}'.format(self._path_prefix, key)

    def get(self, key):
        (value, meta) = self._etcd.get(self.make_path(key))
        return value

    def set(self, key, value):
        self._etcd.put(self.make_path(key), value)

    def delete(self, key):
        success = self._etcd.delete(self.make_path(key))
        return success
