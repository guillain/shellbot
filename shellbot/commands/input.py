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

from .base import Command


class Input(Command):
    """
    Displays input data
    """

    keyword = u'input'
    information_message = u'Display all input'

    no_input_message = u'There is nothing to display'
    input_header =u'Input:'

    def execute(self, bot, arguments=None):
        """
        Displays input data

        :param bot: The bot for this execution
        :type bot: Shellbot

        :param arguments: The arguments for this command
        :type arguments: str or ``None``

        """
        input = bot.recall('input')
        if input in (None, {}):
            bot.say(self.no_input_message)
            return

        lines = [self.input_header]
        for key in sorted(input.keys()):
            lines.append(u"{} - {}".format(key, input.get(key, '')))

        bot.say('\n'.join(lines))
