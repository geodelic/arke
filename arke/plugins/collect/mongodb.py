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

import logging

logger = logging.getLogger(__name__)

import pymongo

from arke.collect import Collect

class mongodb(Collect):
    default_config = {'interval': 30,
                      'host': 'localhost',
                      'port': 27017,
                     }

    def collect(self):
        if not hasattr(self, 'connection'):
            self.connection = pymongo.Connection(
                self.get_setting('host'),
                self.get_setting('port', opt_type=int),
                slave_okay=True,
            )
        connection = self.connection

        db = connection.admin

        try:
            repl_status = db.command('replSetGetStatus')
        except pymongo.errors.OperationFailure:
            logger.debug("Mongodb server is not part of a replica set")
            repl_status = None

        try:
            return dict(
                server_status=db.command('serverStatus'),
                repl_status=repl_status,
                col_stats=dict(self._coll_stats(connection))
            )
        except Exception:
            logger.exception("Error while collecting mongodb server status")

    def _coll_stats(self, connection):
        logger.debug("Collecting mongodb collection status")
        for db_name in connection.database_names():
            if db_name in ('admin', 'local'):
                continue
            colls = {}
            db = connection[db_name]
            for coll_name in db.collection_names():
                if coll_name in ('system.indexes',):
                    continue
                colls[coll_name] = db.command('collstats', coll_name)

            if colls:
                yield (db_name, colls)


if __name__ == '__main__':
    from sys import argv
    try:
        host = argv[1]
    except IndexError:
        host = None
    else:
        try:
            port = argv[2]
        except IndexError:
            port = None

    if host:
        mongodb.default_config['host'] = host
        if port:
            mongodb.default_config['port'] = port

    data = mongodb().collect()
    from pprint import pprint
    pprint(data)

