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


class ipersist(object):
    def __init__(self, config_parser):
        self.config = config_parser
        self.section = 'backend:%s' % self.__class__.__name__.replace('_backend', '')

    def batch_write(self, spool_file):
        raise NotImplemented

    def write(self, sourcetype, timestamp, data, hostname, extra):
        """
        If the write fails (tbd by implementation), return False so the
        runner knows to reschedule.
        Otherwise return True
        """
        raise NotImplemented

