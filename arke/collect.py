#
#   Copyright 2013 Geodelic
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License. 
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. 
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
#

import json
from datetime import datetime
from time import time
import logging
logger = logging.getLogger(__name__)

from bson import json_util, BSON

from gevent.core import timer

class Collect(object):
    default_config = {'interval': 30}
    normalize = False
    format = 'extjson'

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance'):
            cls._instance = super(Collect, cls).__new__(
                                cls, *args, **kwargs)
        return cls._instance

    def get_setting(self, setting, fallback=None, opt_type=None):
        val = None
        if self.config is not None and self.config.has_option(self.section, setting):
            try:
                getter = {int: 'getint',
                          float: 'getfloat',
                          bool: 'getboolean',
                         }[opt_type]
            except KeyError:
                getter = 'get'
            val = getattr(self.config, getter)(self.section, setting)

        if val is None:
            #logger.debug("setting value is None. using defaults.")
            val = self.default_config.get(setting, fallback)
            if not (opt_type in (None, bool) or isinstance(val, opt_type)):
                try:
                    val = opt_type(val)
                except ValueError:
                    pass

        return val

    def __init__(self, config, persist_queue, spool, pool):
        self._pool = pool
        self.spool = spool
        self.config = config
        self.persist_queue = persist_queue
        self.name = self.__class__.__name__
        self.section = 'plugin:%s' % self.name
        if not hasattr(self, '_timer'):
            self._timer = None
        if not hasattr(self, 'is_activated'):
            self.is_activated = False
        assert 'interval' in self.default_config, (
            "Missing default interval value for %s plugin" % self.name)

    @property
    def enabled(self):
        return self.get_setting('enabled', False, opt_type=bool)

    def activate(self):
        self.is_activated = True
        self.run()

    def deactivate(self):
        self.is_activated = False
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None

    def _reset_timer(self):
        assert self._timer is None, "Trying to reset active timer!"

        t = time()
        s = self.get_setting('interval', opt_type=int)
        if self.normalize:
            s = (s - (t % s))

        self._timer = timer(s, self._pool.spawn, self.run)

    def run(self):
        self._timer = None
        logger.debug("Doing run for %s plugin." % self.name)
        try:
            self.gather_data()
        finally:
            self._reset_timer()


    def gather_data(self):
        timestamp = datetime.utcnow()
        sourcetype = self.name
        extra = {
        }

        try:
            data = self.collect()
            logger.debug("Data collection for %s plugin completed" % self.name)
        except Exception:
            logger.exception("error occurred while gathering data for sourcetype %s" % sourcetype)
            return

        logger.debug("sourcetype: %r, timestamp: %s, extra: %r" % (sourcetype, timestamp, extra))
        self.spool.append(sourcetype, timestamp, data, extra)

    def serialize(self, data):
        if not self.format:
            return data

        if self.format.lower() == "json":
            return json.dumps(data)
        elif self.format.lower() == "bson":
            return BSON.encode(data)
        elif self.format.lower() == "extjson":
            return json.dumps(data, default=json_util.default)

