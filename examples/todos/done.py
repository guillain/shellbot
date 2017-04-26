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

from shellbot import Command

class Done(Command):
    """
    Archives an item from the todo list

    >>>command = Done(store=store)
    >>>shell.load_command(command)

    """

    keyword = u'done'
    information_message = u'Archive an item from the todo list'
    usage_message = u'done [#<n>]'
    store = None

    def execute(self, arguments=None):
        """
        Archives an item from the todo list
        """
        if self.store is None:
            raise AttributeError(u'Todo store has not been initialised')

        if arguments in (None, ''):
            index = 1
        else:
            index = self.store.parse(arguments)

        if index is None:
            self.bot.say(u"usage: {}".format(self.usage_message))
            return

        if index > len(self.store.items):
            self.bot.say(u"Nothing to do yet.")

        else:
            self.store.complete(index)
            self.bot.say(u"#{} has been archived".format(index))
