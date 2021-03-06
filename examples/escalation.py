#!/usr/bin/env python
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

"""
Push a button to start interactions

In this example an external event is captured via a web request. This creates
a collaborative place where multiple persons can participate.

Then following commands are available from the bot:

- command: escalate
- response describes the name and characteristics of new state

- command: state
- response describes current state

- command: close
- responses describes the proper archiving of the room


Multiple questions are adressed in this example:

- How to create a room on some external event? Here we wait for a link to be
  triggered over the internet. This can done directly from the command line
  with CURL, from a web browser, or from a button connected to the internet, or
  from an application on a mobile device. When this occurs, a room is created,
  moderators and participants are added, and people can interact immediately.
  Look at the class ``Trigger`` below, and at the bottom of the script, to see
  how this is implemented.

- How to implement a linear process? The typical use case is to let joining
  people interact in the room, then involve some support experts, then
  call stakeholders for a decision. These are reflected in the chat room
  with commands ``state`` and ``next``. Related code is in the ``steps``
  subdirectory.


A typical dialog could be like the following::

    > shelly next

    New state: Level 1 - Initial capture of information
    If you are on the shop floor:
    - Take a picture of the faulty part
    - Describe the issue in the chat box

    As a Stress engineer, engage with shop floor and ask questions. To engage
    with the design team, type next in the chat box.

    > shelly next

    New state: Level 2 - Escalation to technical experts

    ...


To run this script you have to provide a custom configuration, or set
environment variables instead::

- ``CHAT_ROOM_MODERATORS`` - Mention at least your e-mail address
- ``CISCO_SPARK_BOT_TOKEN`` - Received from Cisco Spark on bot registration
- ``CISCO_SPARK_TOKEN`` - Your personal Cisco Spark token
- ``SERVER_URL`` - Public link used by Cisco Spark to reach your server

The token is specific to your run-time, please visit Cisco Spark for
Developers to get more details:

    https://developer.ciscospark.com/

The other token should be associated to a human being, and not to a bot.
This is required so that the software can receive all events for a chat space.
Without it, only messages sent to the bot will be audited.

For example, if you run this script under Linux or macOs with support from
ngrok for exposing services to the Internet::

    export CHAT_ROOM_MODERATORS="alice@acme.com"
    export CISCO_SPARK_BOT_TOKEN="<token id from Cisco Spark for Developers>"
    export CISCO_SPARK_TOKEN="<personal token id from Cisco Spark>"
    export SERVER_URL="http://1a107f21.ngrok.io"
    python escalation.py


"""

import logging
import os
from multiprocessing import Process, Queue
import time

from shellbot import ShellBot, Context, Server, Notify, Wrap
Context.set_logger()

#
# load configuration
#
settings = {

    'bot': {
        'on_start': 'Welcome to this on-demand collaborative room',
        'on_stop': 'Bot is now quitting the room, bye',
    },

    'spark': {
        'room': '[' + os.environ["POD_NAME"] + '] On-demand Collaboration',
        'moderators': os.environ["CHAT_ROOM_MODERATORS"],
    },

    'server': {
        'url':     os.environ["SERVER_URL"],
        'trigger': os.environ["SERVER_TRIGGER"],
        'hook':    os.environ["SERVER_HOOK"],
        'binding': os.environ["SERVER_HOST"],
        'port':    os.environ["SERVER_PORT"],
    },

    'process.steps': [

        {
            'label': u'Level 1',
            'message': u'Initial capture of information',

            'content': u'If you are on the shop floor:\n'
                + u'* Take a picture of the faulty part\n'
                + u'* Describe the issue in the chat box\n'
                + u'\n'
                + u' Use the command **help** for a list of all available commands.'
                + u' Use the command **step** when ready to progress in the process.',
            'participants': os.environ["SHOP_FLOOR"],
        },

        {
            'label': u'Level 2',
            'message': u'Escalation to technical experts',

            'content': u'This is a convenient place to interact in real-time across participants:\n'
                + u'* Via the chat system\n'
                + u'* Share a picture or attach a file\n'
                + u'* Use the Call function for an ad hoc video session\n'
                + u'\n'
                + u'As a Stress engineer, engage with shop floor and ask questions.'
                + u' Use the command **input** to check data captured earlier.'
                + u' Use the command **step** when ready to progress in the process.',

            'participants': os.environ["STRESS_ENGINEER"],
        },

        {
            'label': u'Level 3',
            'message': u'Escalation to decision stakeholders',

            'content': u'This is a convenient place to gather information required to make a decision:\n'
                + u'* Via the chat system\n'
                + u'* Share a picture or attach a file\n'
                + u'* Use the Call function for an ad hoc video session\n'
                + u'\n'
                + u' Use the command **step** when ready to progress in the process.',

            'participants': os.environ["DESIGN_ENGINEER"],
        },

        {
            'label': u'Terminated',
            'message': u'Process is closed, yet conversation can continue',

            'content': u' Use the command **close** when this space can be deleted.',

        },

    ],

}

context = Context(settings)
context.check('server.trigger', os.environ["SERVER_TRIGGER"])
context.check('server.hook', os.environ["SERVER_HOOK"])

#
# create a bot and load commands
#

bot = ShellBot(context=context, configure=True)

bot.load_command('shellbot.commands.close') # allow space deletion from chat

#
# audit all interactions in a separate file
#

from shellbot.commands import Audit
audit = Audit(bot=bot)
bot.load_command(audit)  # manage auditing

from shellbot.updaters import FileUpdater
audit.arm(updater=FileUpdater(path=(os.environ["SERVER_LOG"])))

#
# ask information from end user
#

bot.load_command('shellbot.commands.input') # reflect information gathered

from shellbot.machines import Input, Sequence

order_id = Input(bot=bot,
                question="PO number please?",
                mask="9999A",
                on_retry="PO number should have 4 digits and a letter",
                on_answer="Ok, PO number has been noted: {}",
                on_cancel="Ok, forget about the PO number",
                tip=20,
                timeout=40,
                key='order_id')

description = Input(bot=bot,
                question="Issue description please?",
                on_retry="Please enter a one-line description of the issue",
                on_answer="Ok, description noted: {}",
                on_cancel="Ok, forget about the description",
                tip=20,
                timeout=40,
                key='description')

sequence = Sequence(machines=[order_id, description])

#
# implement the escalation process
#

bot.load_command('shellbot.commands.step') # progress to next step of process

steps = bot.get('process.steps', [])

steps[0]['machine'] = sequence

from shellbot.machines import Steps
bot.machine = Steps(bot=bot, steps=steps)

#
# a queue of events between the web server and the bot
#

queue = Queue()

#
# create a web server to receive triggers and updates
#

server = Server(context=context, check=True)

server.add_route(Notify(queue=queue,
                        route=context.get('server.trigger')))

server.add_route(Wrap(callable=bot.get_hook(),
                      route=context.get('server.hook')))

#
# delay the creation of a room until we receive some trigger
#

class Trigger(object):

    EMPTY_DELAY = 0.005   # time to wait if queue is empty

    def __init__(self, bot, queue):
        self.bot = bot
        self.queue = queue if queue else Queue()

    def start(self):
        p = Process(target=self.run)
        p.start()
        return p

    def run(self):

        logging.info(u"Waiting for trigger")

        try:
            self.bot.context.set('trigger.counter', 0)
            while self.bot.context.get('general.switch', 'on') == 'on':

                if self.queue.empty():
                    time.sleep(self.EMPTY_DELAY)
                    continue

                try:
                    item = self.queue.get(True, self.EMPTY_DELAY)
                    if isinstance(item, Exception):
                        break

                    self.process(item)

                except Exception as feedback:
                    logging.exception(feedback)

        except KeyboardInterrupt:
            pass

    def process(self, item):

        counter = self.bot.context.increment('trigger.counter')
        logging.info(u'Trigger {} {}'.format(item, counter))

        if counter == 1:
            self.bot.bond()
            self.bot.space.on_run()
            self.bot.hook()

            time.sleep(2)
            self.bot.machine.reset()
            self.bot.machine.start()

        else:
            self.bot.say(u'{} {}'.format(item, counter))

    def on_dispose(self):
        logging.debug(u"- stopping the machine")
        self.bot.machine.stop()
        logging.debug(u"- resetting the counter of button pushes")
        self.bot.set('trigger.counter', 0)


trigger = Trigger(bot, queue)

bot.register('dispose', trigger)

#
# launch multiple processes to do the job
#

bot.start()
trigger.start()

server.run()

