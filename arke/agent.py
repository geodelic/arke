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

from gevent import monkey, spawn, sleep
monkey.patch_all(httplib=True, thread=False)

from Queue import Empty, Queue
import logging
import signal

logger = logging.getLogger(__name__)

from simpledaemon import Daemon
from gevent.pool import Pool



from arke.collect import Collect
from arke.plugin import CollectPlugins
from arke.spool import Spooler
from arke.plugins import persist


RETRY_INTERVAL_CAP = 300
DEFAULT_CONFIG_FILE = '/etc/arke/arke.conf'

GATHER_POOL_WORKERS = 1000
PERSIST_POOL_WORKERS = 10


class NoPlugins(Exception): pass

class agent_daemon(Daemon):
    default_conf = '/etc/arke/arke.conf'
    section = 'agent'

    def read_basic_config(self):
        super(agent_daemon, self).read_basic_config()
        self.hostname = self.config_parser.get('core', 'hostname')

    def __init__(self):
        self.persist_queue = Queue()
        self.spool = None
        self.stop_now = False

    def on_sighup(self, signalnum, frame):
        logging.info("got sighup")
        self.config_parser.read(self.config_filename)
        self.collect_manager.load(pool=self._gather_pool)

    def on_sigterm(self, signalnum, frame):
        logging.info("got sigterm")
        self.stop_now = True

    def shutdown(self):
        [x.deactivate() for x in self.collect_manager._plugins if x._timer is not None]
        self._gather_pool.join()
        self.spool.close()

    def add_signal_handlers(self):
        super(self.__class__, self).add_signal_handlers()
        signal.signal(signal.SIGHUP, self.on_sighup)
        signal.signal(signal.SIGINT, self.on_sigterm)

    def run(self):
        logging.debug("initializing spool")
        self.spool = spool = Spooler(self.config_parser)
        self._gather_pool = pool = Pool(GATHER_POOL_WORKERS)

        config = self.config_parser
        persist_queue = self.persist_queue

        self.collect_manager = CollectPlugins(base_class=Collect,
                                              config=config,
                                              init_args=(config, persist_queue, spool, pool),
                                             entry_points='arke_plugins',
                                            )

        self.collect_manager.load(pool=self._gather_pool)
        try:
            self.persist_runner()
        except KeyboardInterrupt:
            pass

        self.shutdown()



    def persist_runner(self):
        logging.debug("initializing backend %s" % self.config_parser.get('core', 'persist_backend'))
        persist_backend = getattr(persist, '%s_backend' %
                self.config_parser.get('core', 'persist_backend'))

        persist_backend = persist_backend(self.config_parser)

        spool = self.spool

        self.persist_pool = pool = Pool(PERSIST_POOL_WORKERS)

        while 1:
            spool_file = None
            if self.stop_now:
                break
            try:
                spool_file = spool.get(5)
            except Empty:
                sleep(1)
                continue

            pool.spawn(self.persist_data, spool_file, persist_backend)

        pool.join()


    def persist_data(self, spool_file, persist_backend):
        if spool_file is None:
            logger.debug("Told to persist spool_file None!")
            return

        attempt = 1
        retry = .2
        while 1:
            if self.stop_now:
                return
            try:
                logging.debug("persisting data- spool_file: %s, attempt: %r" % (spool_file.name, attempt))
                persist_backend.batch_write(spool_file)
                break
            except Exception:
                logging.exception("attempt %s trying to persist spool_file: %s" % (attempt, spool_file.name))

            sleep(retry)
            if retry < RETRY_INTERVAL_CAP:
                retry = attempt * 2
            attempt += 1

        self.spool.delete(spool_file)


if __name__ == '__main__':
    agent_daemon().main()

