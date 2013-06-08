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

from time import time
import logging

logger = logging.getLogger(__name__)

from gevent.socket import create_connection
from gevent.server import StreamServer
from gevent import spawn

from arke.plugins.collect._multi import MultiCollect

class latency(MultiCollect):
    default_config = {'interval': 10,
                      'port': 64007,
                      'server_concurrency': 1000,
                      'server_backlog': 2048,
                      'region': None,
                     }

    def activate(self):
        super(latency, self).activate()
        self._start_server()

    def deactivate(self):
        super(latency, self).deactivate()
        self._server.kill()

    def _start_server(self):
        def handler(sock, client_addr):
            logger.debug("Got connection from: %s" % ':'.join(map(str, client_addr)))
            sock.recv(5)
            sock.sendall('PONG\n')
        self._server = StreamServer(
                         ('0.0.0.0', self.get_setting('port', opt_type=int)),
                         handle=handler,
                         backlog=self.get_setting('server_backlog', opt_type=int))
        spawn(self._server.serve_forever)


    def _collect(self, server, start, host):
        sock = create_connection((host, self.get_setting('port', opt_type=int)))
        sock.sendall('PING\n')
        sock.recv(5)
        return time() - start



if __name__ == '__main__':
    from pprint import pprint
    p = latency()
    p._start_server()
    pprint(p.collect({'fqdn': 'localhost'}, 'localhost'))

