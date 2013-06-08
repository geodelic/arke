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

import httplib
import logging
import json

logger = logging.getLogger(__name__)

from bson import json_util

from .base import ipersist

class http_backend(ipersist):
    content_type_map = {'json': 'application/json',
                        'extjson': 'application/extjson',
                        'bson': 'application/bson',
                       }

    def __init__(self, *args, **kwargs):
        super(http_backend, self).__init__(*args, **kwargs)
        self.host = self.config.get(self.section, 'host')
        self.port = None
        if self.config.has_option(self.section, 'port'):
            self.port = self.config.getint(self.section, 'port')
        if self.config.has_option('core', 'debug'):
            self.debug = self.config.getboolean('core', 'debug')
        else:
            self.debug = False

    def get_connection(self):
        return httplib.HTTPConnection(self.host, self.port)

    def write(self, sourcetype, timestamp, data, hostname, extra):
        conn = self.get_connection()
        uri = '/store/%s/%s/%f' % (hostname, sourcetype, timestamp)

        headers = {}
        if extra and isinstance(extra, dict):
            if extra.get('ctype', None):
                headers['Content-type'] = self.content_type_map[extra['ctype']]
            headers['extra'] = json.dumps(extra, default=json_util.default)

        conn.request('POST', uri, body=data, headers=headers)
        resp = conn.getresponse()

        assert resp.status in (200,204), "Didn't get 200 from remote server!"


    def batch_write(self, spool_file):
        spool_file.seek(0)
        conn = self.get_connection()
        uri = '/batch_store'
        headers = {}
        conn.request('POST', uri, body=spool_file, headers=headers)
        resp = conn.getresponse()

        assert resp.status in (200,204), "Didn't get 200 from remote server!"

