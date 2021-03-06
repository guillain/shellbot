# -*- coding: utf-8 -*-

# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
from multiprocessing import Process, Queue
from six import string_types
import time


class Vibes(object):
    def __init__(self, text=None, content=None, file=None, space_id=None):
        self.text = text
        self.content = content
        self.file = file
        self.space_id=space_id

    def __str__(self):
        """
        Returns a human-readable string representation of this object.
        """
        return u"text={}, content={}, file={}, space_id={}".format(
            self.text, self.content, self.file, self.space_id)


class Speaker(object):
    """
    Sends updates to a business messaging space
    """

    EMPTY_DELAY = 0.005   # time to wait if queue is empty
    NOT_READY_DELAY = 5   # time to wait if space is not ready

    def __init__(self, engine=None):
        """
        Sends updates to a business messaging space

        :param engine: the overarching engine
        :type engine: Engine

        """
        self.engine = engine

    def start(self):
        """
        Starts the speaking process

        :return: either the process that has been started, or None

        This function starts a separate daemonic process to speak
        in the background.
        """
        process = Process(target=self.run)
        process.daemon = True
        process.start()
        return process

    def run(self):
        """
        Continuously send updates

        This function is looping on items received from the queue, and
        is handling them one by one in the background.

        Processing should be handled in a separate background process, like
        in the following example::

            speaker = Speaker(engine=my_engine)
            process_handle = speaker.start()

        The recommended way for stopping the process is to change the
        parameter ``general.switch`` in the context. For example::

            engine.set('general.switch', 'off')

        Alternatively, the loop is also broken when an exception is pushed
        to the queue. For example::

            engine.mouth.put(Exception('EOQ'))

        Note that items are not picked up from the queue until the underlying
        space is ready for handling messages.
        """
        logging.info(u"Starting speaker")

        try:
            self.engine.set('speaker.counter', 0)
            not_ready_flag = True
            while self.engine.get('general.switch', 'on') == 'on':

                if self.engine.mouth.empty():
                    time.sleep(self.EMPTY_DELAY)
                    continue

                try:
                    item = self.engine.mouth.get(True, 0.1)
                    if item is None:
                        break

                    self.process(item)

                except Exception as feedback:
                    logging.exception(feedback)

        except KeyboardInterrupt:
            pass

        logging.info(u"Speaker has been stopped")

    def process(self, item):
        """
        Sends one update to a business messaging space

        :param item: the update to be transmitted
        :type item: str or object

        """

        counter = self.engine.context.increment('speaker.counter')
        logging.debug(u'Speaker is working on {}'.format(counter))

        if self.engine.space is not None:
            if isinstance(item, string_types):
                self.engine.space.post_message(item)
            else:
                self.engine.space.post_message(item.text,
                                               content=item.content,
                                               file=item.file,
                                               space_id=item.space_id)
        else:
            logging.info(item)
