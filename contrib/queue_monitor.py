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

from arke.collect import Collect

class queue_monitor(Collect):
    default_config = {'interval': 60,
                     }

    def gather_data(self):
        logger.info("persist_queue: %i, collect_pool: %i" % (self.persist_queue.qsize(), len(self._pool)))

