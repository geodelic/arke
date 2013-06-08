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

from socket import create_connection
from paramiko.transport import Transport, SSHException

from arke.plugins.collect._multi import MultiCollect

class ssh_hello(MultiCollect):
    default_config = {'interval': 10,
                      'port': 22,
                      'region': None,
                     }

    def _collect(self, server, start, host):
        try:
            sock = create_connection((host, self.get_setting('port', opt_type=int)))

            transport = Transport(sock)
            transport.logger.setLevel(logging.WARNING)
            transport.packetizer.write_all(transport.local_version + '\r\n')
            transport._check_banner()
            transport.packetizer.close()

            lag = time() - start
        except SSHException, e:
            logger.info('ssh exception: %s for server %s' % (e, server['fqdn']))
            lag = -1

        return lag



if __name__ == '__main__':
    from sys import argv
    port = 22
    try:
        host = argv[1]
    except IndexError:
        host = 'localhost'
    else:
        try:
            port = argv[2]
        except IndexError:
            pass

    ssh_hello.default_config['port'] = port

    from pprint import pprint
    p = ssh_hello()
    pprint(p.collect({'fqdn': host}, 'hostname'))

