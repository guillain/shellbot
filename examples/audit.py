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
Audit interactions in real-time

In this example we create a shell with one simple command: audit

- command: audit
- provides clear status if this room is currently audited or not

- command: audit on
- starts auditing

- command: audit off
- ensure private interactions for some time


To run this script you have to provide a custom configuration, or set
environment variables instead::

- ``CHAT_ROOM_MODERATORS`` - Mention at least your e-mail address
- ``CISCO_SPARK_BOT_TOKEN`` - Received from Cisco Spark on bot registration
- ``CISCO_SPARK_TOKEN`` - Your personal Cisco Spark token
- ``SERVER_URL`` - Public link used by Cisco Spark to reach your server

The bot token is specific to your run-time, please visit Cisco Spark for
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
    python hello.py


"""

import logging
from multiprocessing import Process, Queue
import os

from shellbot import ShellBot, Context, Command, Speaker
from shellbot.commands import Audit
from shellbot.spaces import SparkSpace
from shellbot.updaters import SpaceUpdater
Context.set_logger()

# create a bot
#
bot = ShellBot()

# add an audit command
#
audit = Audit(bot=bot)
bot.load_command(audit)

# load configuration
#
os.environ['CHAT_ROOM_TITLE'] = 'Audit tutorial'
bot.configure()

# create a chat room
#
bot.bond(reset=True)

# create a mirror chat room
#
mirror_bot = ShellBot()
mirror_bot.configure()
mirror = SparkSpace(bot=mirror_bot)
mirror.connect()

title = u"{} - {}".format(
    mirror.configured_title(), u"Audited content")

mirror.bond(title=title)

# enable auditing
#
audit.arm(updater=SpaceUpdater(space=mirror))

# run the bot
#
bot.run()

# delete chat rooms when the bot is stopped
#
mirror.delete_space()
bot.dispose()
