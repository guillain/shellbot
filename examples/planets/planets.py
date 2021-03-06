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

from .mission import Mission

class Planets(Mission):
    """
    Displays the list of available planets

    >>>command = Planets()
    >>>shell.load_command(command)

    """

    keyword = u'planets'
    information_message = u'List reachable planets'
    list_header = u"Available destinations:"
    is_interactive = True

    def execute(self, bot, arguments=None):
        """
        Displays the list of available planets
        """

        items = self.get_planets(bot)
        if len(items):
            bot.say(self.list_header
                    + '\n- ' + '\n- '.join(items))
        else:
            bot.say(u"Nowhere to go right now.")
