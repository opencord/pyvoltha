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

"""Setting up proper logging for Voltha"""

from __future__ import absolute_import
import builtins # bring in python 2 to 3 compat imports: https://python-future.org/imports.html
import json
import logging
import logging.config
from collections import OrderedDict

import structlog
from structlog.stdlib import BoundLogger, INFO

try:
    from _thread import get_ident as _get_ident
except ImportError:
    from _dummy_thread import get_ident as _get_ident


class StructuredLogRenderer(object):
    def __call__(self, logger, name, event_dict):
        # in order to keep structured log data in event_dict to be forwarded as
        # is, we need to pass it into the logger framework as the first
        # positional argument.
        args = (event_dict,)
        kwargs = {}
        return args, kwargs


class EncoderFix(json.JSONEncoder):
    def default(self, obj):
        return str(obj)


class JsonRenderedOrderedDict(OrderedDict):
    """Our special version of OrderedDict that renders into string as a dict,
       to make the log stream output cleaner.
    """
    def __repr__(self, _repr_running=None):
        # od.__repr__() <==> repr(od)
        call_key = id(self), _get_ident()
        _repr_running = _repr_running or dict()

        if call_key in _repr_running:
            return '...'

        _repr_running[call_key] = 1
        try:
            if not self:
                return ''

            # Convert to JSON but strip off outside '{}'
            msg = '"msg":"{}",'.format(self.pop('event'))
            json_msg = json.dumps(self, indent=None,
                                  cls=EncoderFix,
                                  separators=(', ', ': '),
                                  sort_keys=True)[1:-1]
            return msg + json_msg

        finally:
            del _repr_running[call_key]


class PlainRenderedOrderedDict(OrderedDict):
    """Our special version of OrderedDict that renders into string as a dict,
       to make the log stream output cleaner.
    """
    def __repr__(self, _repr_running={}):
        'od.__repr__() <==> repr(od)'
        call_key = id(self), _get_ident()
        if call_key in _repr_running:
            return '...'
        _repr_running[call_key] = 1
        try:
            if not self:
                return '{}'
            return '{%s}' % ", ".join("%s: %s" % (k, v)
                                      for k, v in self.items())
        finally:
            del _repr_running[call_key]


def setup_logging(log_config, instance_id, verbosity_adjust=0):
    """
    Set up logging such that:
    - The primary logging entry method is structlog
      (see http://structlog.readthedocs.io/en/stable/index.html)
    - By default, the logging backend is Python standard lib logger
    """

    def add_exc_info_flag_for_exception(_, name, event_dict):
        if name == 'exception':
            event_dict['exc_info'] = True
        return event_dict

    def add_instance_id(_, __, event_dict):
        event_dict['instance_id'] = instance_id
        return event_dict

    # Configure standard logging
    logging.config.dictConfig(log_config)
    logging.root.level = verbosity_adjust

    processors = [
        add_exc_info_flag_for_exception,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        add_instance_id,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ]
    structlog.configure(logger_factory=structlog.stdlib.LoggerFactory(),
                        context_class=JsonRenderedOrderedDict,
                        wrapper_class=BoundLogger,
                        processors=processors)

    # Mark first line of log
    log = structlog.get_logger()
    log.info("first-line", log_level=logging.root.level, verbosity_adjust=verbosity_adjust)
    return log


def string_to_int(loglevel):
    l = loglevel.upper()
    if l == "DEBUG": return 10
    elif l == "INFO": return 20
    elif l == "WARN": return 30
    elif l == "ERROR": return 40
    elif l == "FATAL": return 50
    else: return 0


def update_logging(instance_id, _vcore_id, verbosity_adjust=0):
    """
    Add the vcore id to the structured logger
    :param vcore_id:  The assigned vcore id
    :return: structure logger
    """
    def add_exc_info_flag_for_exception(_, name, event_dict):
        if name == 'exception':
            event_dict['exc_info'] = True
        return event_dict

    def add_instance_id(_, __, event_dict):
        event_dict['instance_id'] = instance_id
        return event_dict

    logging.root.level = verbosity_adjust

    processors = [
        add_exc_info_flag_for_exception,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        add_instance_id,
        StructuredLogRenderer(),
    ]
    structlog.configure(processors=processors)

    # Mark first line of log
    log = structlog.get_logger()
    log.info("updated-logger")
    return log
