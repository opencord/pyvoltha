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
from twisted.internet import threads

import etcd3

class TwistedEtcdStore(object):

    def __init__(self, host, port, path_prefix):
        self._etcd = etcd3.client(host=host, port=port)
        self.host = host
        self.port = port
        self._path_prefix = path_prefix

    def make_path(self, key):
        return '{}/{}'.format(self._path_prefix, key)

    def get(self, key):

        def success(results):
            (value, meta) = results
            return value

        def failure(exception):
            raise exception

        deferred = threads.deferToThread(self._etcd.get, self.make_path(key))
        deferred.addCallback(success)
        deferred.addErrback(failure)
        return deferred

    def set(self, key, value):

        def success(results):
            if results:
                return results
            else:
                return False

        def failure(exception):
            raise exception

        deferred = threads.deferToThread(self._etcd.put, self.make_path(key), value)
        deferred.addCallback(success)
        deferred.addErrback(failure)
        return deferred

    def watch(self, key, callback):

        def success(results):
            return results

        def failure(exception):
            raise exception

        deferred = threads.deferToThread(self._etcd.add_watch_callback, self.make_path(key), callback)
        deferred.addCallback(success)
        deferred.addErrback(failure)
        return deferred

    def delete(self, key):

        def success(results):
            if results:
                return results
            else:
                return False

        def failure(exception):
            raise exception

        deferred = threads.deferToThread(self._etcd.delete, self.make_path(key))
        deferred.addCallback(success)
        deferred.addErrback(failure)
        return deferred
