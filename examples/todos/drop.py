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

class Drop(Command):
    """
    Deletes an item from the todo list

    >>>command = Drop()
    >>>shell.load_command(command)

    """

    keyword = u'drop'
    information_message = u'Delete an item from the todo list'
    usage_message = u'drop [#<n>]'

    def execute(self, bot, arguments=None):
        """
        Deletes an item from the todo list
        """
        if self.engine.factory is None:
            raise AttributeError(u'Todo factory has not been initialised')

        if arguments in (None, ''):
            index = 1
        else:
            index = self.engine.factory.parse(arguments)

        if index is None:
            bot.say(u"usage: {}".format(self.usage_message))
            return

        if index > len(self.engine.factory.items):
            bot.say(u"Nothing to do yet.")

        else:
            self.engine.factory.delete(index)
            bot.say(u"#{} has been deleted".format(index))
