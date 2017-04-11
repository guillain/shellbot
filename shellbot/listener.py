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

import json
import logging
from Queue import Empty
import random
import time

class Listener(object):
    """
    Handles messages received from chat space
    """

    def __init__(self, ears, shell, tee=None):
        """
        Handles messages received from chat space

        :param ears: the queue of messages
        :type ears: queue

        :param shell: the shell that will handle commands
        :type shell: shell

        :param tee: if provided, messages received are duplicated there
        :type tee: queue

        """
        self.ears = ears
        self.shell = shell
        self.tee = tee

    def work(self, context):
        """
        Continuously receives updates

        :param context: the context shared across processes
        :type context: context

        This function is looping on items received from the queue, and
        is handling them one by one in the background.

        Processing should be handled in a separate background process, like
        in the following example::

            listener = Listener(ears=ears, shell=shell)

            process = Process(target=listener.work, args=(context,))
            process.daemon = True
            process.start()

        The recommended way for stopping the process is to change the
        parameter ``general.switch`` in the context. For example::

            context.set('general.switch', 'off')

        Alternatively, the loop is also broken when an exception is pushed
        to the queue. For example::

            ears.put(Exception('EOQ'))

        """
        logging.info("Starting listener")

        self.context = context

        self.context.set('listener.counter', 0)
        while self.context.get('general.switch', 'on') == 'on':
            try:
                item = self.ears.get(True, 0.1)
                if isinstance(item, Exception):
                    break
                counter = self.context.increment('listener.counter')
                self.process(item, counter)
            except Empty:
                pass

        logging.info("Listener has been stopped")

    def process(self, item, counter):
        """
        Processes bits coming from Cisco Spark

        :param item: the message received
        :type item: dict

        :param counter: number of items processed so far
        :type counter: int

        This function listens for specific commands in the coming flow.
        When a command has been identified, it is acknowledged immediately.
        Commands that require significant processing time are pushed
        to the inbox.

        Example command received from Cisco Spark:

            {
              "id" : "Z2lzY29zcGFyazovL3VzL01FU1NBR0UvOTJkYjNiZTAtNDNiZC0xMWU2LThhZTktZGQ1YjNkZmM1NjVk",
              "roomId" : "Y2lzY29zcGFyazovL3VzL1JPT00vYmJjZWIxYWQtNDNmMS0zYjU4LTkxNDctZjE0YmIwYzRkMTU0",
              "roomType" : "group",
              "toPersonId" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mMDZkNzFhNS0wODMzLTRmYTUtYTcyYS1jYzg5YjI1ZWVlMmX",
              "toPersonEmail" : "julie@example.com",
              "text" : "/plumby use containers/docker",
              "personId" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mNWIzNjE4Ny1jOGRkLTQ3MjctOGIyZi1mOWM0NDdmMjkwNDY",
              "personEmail" : "matt@example.com",
              "created" : "2015-10-18T14:26:16+00:00",
              "mentionedPeople" : [ "Y2lzY29zcGFyazovL3VzL1BFT1BMRS8yNDlmNzRkOS1kYjhhLTQzY2EtODk2Yi04NzllZDI0MGFjNTM", "Y2lzY29zcGFyazovL3VzL1BFT1BMRS83YWYyZjcyYy0xZDk1LTQxZjAtYTcxNi00MjlmZmNmYmM0ZDg" ]
            }

        """
        logging.info('Listener is working on {}'.format(counter))

        if self.tee:
            self.tee.put(item)

        # sanity check
        #
        if not isinstance(item, dict) or 'personId' not in item.keys():
            logging.info("- not a dict, thrown away")
            return

        input = item.get('text', '')
        if input is None:
            logging.info("- no input in this item, thrown away")
            return

        # my own messages
        #
        if item['personId'] == self.context.get('spark.bot_id'):
            logging.info("- sent by me, thrown away")
            return

#        print(item)

        # we can be called with 'plumby ...' or '@plumby ...' or '/plumby ...'
        #
        if input[0] in ['@', '/']:
            input = input[1:]

        bot = self.shell.name.lower()
        if not input.lower().startswith(bot):
            try:
                logging.info("- {}".format(input))
            except:
                pass
            logging.info("- not for me, thrown away")
            return

        line = input[len(bot):].strip()

        self.shell.do(line)
