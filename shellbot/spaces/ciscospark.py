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

from bottle import request
import logging
from multiprocessing import Process, Queue
import os
import re
import requests
from six import string_types
import tempfile
import time

from shellbot.events import Event, Message, Attachment, Join, Leave
from .base import Space


class SparkSpace(Space):
    """
    Handles a Cisco Spark room

    This is a representation of a chat space hosted at Cisco Spark.

    In normal mode of usage, two tokens whould be provided, one for
    the Cisco Spark bot, and one for a regular Cisco Spark account. This
    allows shellbot to see all the traffic coming from the chat room, even
    messages sent to other chat participants.

    If only the Cisco Spark bot token is provided, then shellbot will get
    visibility and rights limited to what Cisco Spark exposes to bots.
    For example, the audit command will see only messages sent to the bot, or
    those where the bot is mentioned. Other messages will not been seen.

    If no Cisco Spark bot token is provided, but only a personal token,
    then shellbot will act entirely on behalf of this account. This is
    equivalent to a full Cisco Spark integration, through direct
    configuration of shellbot.

    The space maintains two separate API instances internally. One
    is bound to the bot token, and another one is bound to the personal token.

    Cisco Spark API is invoked with one or the other, depending on the role
    played by shellbot:

    - list rooms - personal token - for lookup before room creation/deletion
    - create room - personal token - similar to what a regular user would do
    - delete room - personal token - rather handled by a human being
    - add moderator - personal token - because bot cannot do it
    - add participant - bot token - explicit bot action
    - remove participant - personal token - because bot cannot always do it
    - post message - bot token - explicit bot action
    - create webhook - personal token - required to receive all messages
    - people me - bot token - retrieve bot information
    - people me - personal token - retrieve administrator information

    If one token is missing, then the other one is used for everything.

    """

    def on_init(self,
                prefix='spark',
                token=None,
                personal_token=None,
                **kwargs):
        """
        Handles extended initialisation parameters

        :param prefix: the main keyword for configuration of this space
        :type prefix: str

        :param token: bot authentication token for the Cisco Spark API
        :type token: str

        :param personal_token: person authentication token for the Cisco Spark API
        :type token: str

        Example::

            space = SparkSpace(bot=bot, prefix='spark.audit')

        Here we create a new space powered by Cisco Spark service, and use
        settings under the key ``spark`` in the context of this bot.
        """
        assert prefix not in (None, '')
        self.prefix = prefix

        if token not in (None, ''):
            self.set('token', token)

        if personal_token not in (None, ''):
            self.set('personal_token', personal_token)

        self.api = None
        self.personal_api = None

    def on_reset(self):
        """
        Resets extended internal variables
        """
        logging.debug(u"- Cisco Spark reset")

        self.teamId = None

        self.token = self.get('token', '')

        self.personal_token = self.get('personal_token', '')

        self._last_message_id = 0

    def check(self):
        """
        Checks settings of the space

        This function reads key ``spark`` and below, and update
        the context accordingly::

           space.configure({'spark': {
               'room': 'My preferred room',
               'moderators':
                  ['foo.bar@acme.com', 'joe.bar@corporation.com'],
               'participants':
                  ['alan.droit@azerty.org', 'bob.nard@support.tv'],
               'team': 'Anchor team',
               'token': '$MY_BOT_TOKEN',
               'personal_token': '$MY_PERSONAL_TOKEN',
               }})

        This can also be written in a more compact form::

           space.configure({'spark.room': 'My preferred room',
               'spark.token': '$MY_BOT_TOKEN',
               'spark.personal_token': '$MY_PERSONAL_TOKEN',
               })

        This function handles following parameters:

        * ``spark.room`` - title of the associated Cisco Spark room.
          This can refer to an environment variable if it starts
          with ``$``, e.g., ``$ROOM_TITLE``.

        * ``spark.moderators`` - list of persons assigned as room moderators
          This can refer to an environment variable if it starts
          with ``$``, e.g., ``$ROOM_MODERATORS``.

        * ``spark.participants`` - list of initial participants

        * ``spark.team`` - title of a team associated with this room

        * ``spark.token`` - private token of the bot, given by Cisco Spark.
          Instead of putting the real value of the token you are encouraged
          to use an environment variable instead,
          e.g., ``$MY_BOT_TOKEN``.
          If ``spark.token`` is not provided, then the function looks for an
          environment variable ``CISCO_SPARK_BOT_TOKEN`` instead.

        * ``spark.personal_token`` - private token of a human being
          Instead of putting the real value of the token you are encouraged
          to use an environment variable instead,
          e.g., ``$MY_PERSONAL_TOKEN``.
          If ``spark.personal_token`` is not provided, then the function looks
          for an environment variable ``CISCO_SPARK_TOKEN`` instead.

        If a single value is provided for ``moderators`` or for
        ``participants`` then it is turned automatically to a list.

        Example::

            >>>space.configure({'spark.moderators': 'bobby@jah.com'})
            >>>space.context.get('spark.moderators')
            ['bobby@jah.com']

        """
        self.context.check(self.prefix+'.room', filter=True)
        self.context.check(self.prefix+'.moderators', [], filter=True)
        self.context.check(self.prefix+'.participants', [])
        self.context.check(self.prefix+'.team')
        self.context.check(self.prefix+'.token',
                           '$CISCO_SPARK_BOT_TOKEN', filter=True)
        self.context.check(self.prefix+'.personal_token',
                           '$CISCO_SPARK_TOKEN', filter=True)

        values = self.context.get(self.prefix+'.moderators')
        if isinstance(values, string_types):
            self.context.set(self.prefix+'.moderators', [values])

        values = self.context.get(self.prefix+'.participants')
        if isinstance(values, string_types):
            self.context.set(self.prefix+'.participants', [values])

    def configured_title(self):
        """
        Returns the title of the space as set in configuration

        :return: the configured title, or ``Collaboration space``
        :rtype: str

        This function should be rewritten in sub-classes if
        space title does not come from ``space.room`` parameter.
        """
        return self.get('room', self.DEFAULT_SPACE_TITLE)

    def connect(self, factory=None, **kwargs):
        """
        Connects to the back-end API

        :parameter factory: an API factory, for test purpose
        :type: object

        This function loads two instances of Cisco Spark API, one using
        the bot token, and one using the personal token. If only one
        token is available, then it is used for both.

        If a factory is provided, it is used to get API instances. Else
        the regular CiscoSparkAPI is invoked instead.

        """
        assert (self.token not in (None, '') or
                self.personal_token not in (None, '')) # some token is needed

        if not factory:
            from ciscosparkapi import CiscoSparkAPI
            factory = CiscoSparkAPI

        self.api = None
        try:
            if self.token:
                logging.debug(u"Loading Cisco Spark API as bot")
                self.api = factory(access_token=self.token)

            else:
                self.api = factory(access_token=self.personal_token)

        except Exception as feedback:
            logging.error(u"Unable to load Cisco Spark API")
            logging.exception(feedback)

        self.personal_api = None
        try:
            if self.personal_token:
                logging.debug(u"Loading Cisco Spark API as person")
                self.personal_api = factory(access_token=self.personal_token)

            else:
                self.personal_api = factory(access_token=self.token)

        except Exception as feedback:
            logging.error(u"Unable to load Cisco Spark API")
            logging.exception(feedback)

        self.on_connect()

    def on_connect(self):
        """
        Retrieves attributes of this bot

        This function queries the Cisco Spark API to remember the id of this
        bot. This is used afterwards to filter inbound messages to the shell.

        """
        assert self.api is not None  # connect() is prerequisite

        count = 2
        while count:
            try:

                logging.debug(u"Retrieving bot information")
                me = self.api.people.me()
#                logging.debug(u"- {}".format(str(me)))

                self.context.set('bot.email', str(me.emails[0]))
                logging.debug(u"- bot email: {}".format(
                    self.context.get('bot.email')))

                self.context.set('bot.name',
                             str(me.displayName))
                logging.debug(u"- bot name: {}".format(
                    self.context.get('bot.name')))

                self.context.set('bot.id', me.id)
                logging.debug(u"- bot id: {}".format(
                    self.context.get('bot.id')))

                break

            except Exception as feedback:
                count -= 1
                if count == 0:
                    logging.warning(u"Unable to retrieve bot id")
                    logging.exception(feedback)
                else:
                    logging.warning(u"Retrying to retrieve bot id")
                time.sleep(0.1)

        assert self.personal_api is not None  # connect() is prerequisite

        count = 2
        while count:
            try:
                logging.debug(u"Retrieving admin information")
                me = self.personal_api.people.me()
#                logging.debug(u"- {}".format(str(me)))

                self.context.set('administrator.email', str(me.emails[0]))
                logging.debug(u"- administrator email: {}".format(
                    self.context.get('administrator.email')))

                self.context.set('administrator.name', str(me.displayName))
                logging.debug(u"- administrator name: {}".format(
                    self.context.get('administrator.name')))

                self.context.set('administrator.id', me.id)
                logging.debug(u"- administrator id: {}".format(
                    self.context.get('administrator.id')))

                break

            except Exception as feedback:
                time.sleep(0.1)
                count -= 1
                if count == 0:
                    logging.warning(u"Unable to retrieve moderator id")
                    logging.exception(feedback)
                else:
                    logging.warning(u"Retrying to retrieve moderator id")

    def use_space(self, id, **kwargs):
        """
        Uses an existing space

        :param id: title of the target space
        :type id: str

        :return: True on success, False otherwise

        If a space already exists with this id, this object is
        configured to use it and the function returns True.

        Else the function returns False.

        """
        assert id not in (None, '')
        logging.info(u"Using Cisco Spark room '{}'".format(id))

        assert self.personal_api is not None  # connect() is prerequisite
        try:
            for room in self.personal_api.rooms.list():
                if id == room.id:
                    logging.info(u"- found it")
                    self.use_room(room)
                    return True

            logging.info(u"- not found")

        except Exception as feedback:
            logging.error(u"Unable to list rooms")
            logging.exception(feedback)

        return False

    def lookup_space(self, title, **kwargs):
        """
        Looks for an existing space by name

        :param title: title of the target space
        :type title: str

        :return: True on successful lookup, False otherwise

        If a space already exists with this title, the object is configured
        to use it and the function returns True.

        Else the function returns False.
        """
        assert title not in (None, '')
        logging.info(u"Looking for Cisco Spark room '{}'".format(title))

        assert self.personal_api is not None  # connect() is prerequisite
        try:
            for room in self.personal_api.rooms.list():
                if title == room.title:
                    logging.info(u"- found it")
                    self.use_room(room)
                    return True

            logging.info(u"- not found")

        except Exception as feedback:
            logging.error(u"Unable to list rooms")
            logging.exception(feedback)

        return False

    def create_space(self, title, ex_team=None, **kwargs):
        """
        Creates a space

        :param title: title of the target space
        :type title: str

        :param ex_team: the team attached to this room (optional)
        :type ex_team: str or object

        If the parameter ``ex_team`` is provided, then it can be either a
        simple name, or a team object featuring an id.

        On successful space creation, this object is configured
        to use it.
        """
        teamId = None
        if ex_team:
            try:
                teamId = ex_team.id
            except:
                teamId = self.get_team(ex_team).id

        logging.info(u"Creating Cisco Spark room '{}'".format(title))

        assert self.personal_api is not None  # connect() is prerequisite
        while True:
            try:
                room = self.personal_api.rooms.create(title=title,
                                                      teamId=teamId)
                logging.info(u"- done")

                self.use_room(room)
                break

            except Exception as feedback:
                if str(feedback).startswith('Response Code [503]'):
                    logging.debug(u'- delayed by server')
                    time.sleep(3)
                    continue

                logging.warning(u"Unable to create room ")
                logging.exception(feedback)
                break

    def use_room(self, room):
        """
        Uses this room for this space

        :param room: the representation to use

        """
        logging.info(u"Bonding to room '{}'".format(room.title))

        self.values['id'] = room.id
        logging.debug(u"- id: {}".format(self.id))

        self.values['title'] = room.title
        logging.debug(u"- title: {}".format(self.title))

        logging.debug(u"- type: {}".format(room.type))
        self.is_direct = True if room.type == "direct" else False
        self.is_group = True if room.type in ("group", "team") else False
        self.is_team = True if room.type == "team" else False

        self.is_locked = True if room.isLocked else False
        logging.debug(u"- is_locked: {}".format(self.is_locked))

        self.team_id = room.teamId

        bot_email = self.context.get('bot.email')
        administrator_email = self.context.get('administrator.email')
        if bot_email != administrator_email:
            logging.debug(u"- adding bot: {}".format(bot_email))
            self.add_moderator(bot_email)

    def delete_space(self, title=None, **kwargs):
        """
        Deletes a Cisco Spark room

        :param title: title of the room to be deleted (optional)
        :type title: str

        >>>space.delete_space("Obsolete Space")

        """
        if title:
            if not self.lookup_space(title=title):  # set self.id & self.title
                logging.debug(u"No room to delete")
                return

        elif self.id and self.title:
            pass

        elif self.lookup_space(title=self.configured_title()):
            pass

        else:
            logging.debug(u"No room to delete")
            return

        logging.info(u"Deleting Cisco Spark room '{}'".format(self.title))
        logging.debug(u"- id: {}".format(self.id))

        assert self.personal_api is not None  # connect() is prerequisite
        try:
            self.personal_api.rooms.delete(roomId=self.id)

        except Exception as feedback:
            logging.warning(u"Unable to delete room")
            logging.exception(feedback)

    def get_team(self, name):
        """
        Gets a team by name

        :param name: name of the target team
        :type name: str

        :return: attributes of the team
        :rtype: Team or None

        >>>print(space.get_team("Hello World"))
        Team({
          "id" : "Y2lzY29zcGFyazovL3VzL1RFQU0Yy0xMWU2LWE5ZDgtMjExYTBkYzc5NzY5",
          "name" : "Hello World",
          "created" : "2015-10-18T14:26:16+00:00"
        })

        """
        logging.info(u"Looking for Cisco Spark team '{}'".format(name))

        assert self.personal_api is not None  # connect() is prerequisite
        for team in self.personal_api.teams.list():
            if name == team.name:
                logging.info(u"- found it")
                return team

        logging.warning(u"- not found")
        return None

    def add_moderator(self, person):
        """
        Adds a moderator

        :param person: e-mail address of the person to add
        :type person: str

        """
        try:
            assert self.personal_api is not None  # connect() is prerequisite
            assert self.id is not None  # bond() is prerequisite

            self.personal_api.memberships.create(roomId=self.id,
                                                 personEmail=person,
                                                 isModerator=True)

        except Exception as feedback:
            logging.warning(u"Unable to add moderator '{}'".format(person))
            logging.exception(feedback)

    def add_participant(self, person):
        """
        Adds a participant

        :param person: e-mail address of the person to add
        :type person: str

        """
        try:
            assert self.api is not None  # connect() is prerequisite
            assert self.id is not None  # bond() is prerequisite

            self.api.memberships.create(roomId=self.id,
                                        personEmail=person)

        except Exception as feedback:
            logging.warning(u"Unable to add participant '{}'".format(person))
            logging.exception(feedback)

    def remove_participant(self, person):
        """
        Removes a participant

        :param person: e-mail address of the person to remove
        :type person: str

        """
        try:
            assert self.personal_api is not None  # connect() is prerequisite
            assert self.id is not None  # bond() is prerequisite

            self.personal_api.memberships.delete(roomId=self.id,
                                                 personEmail=person)

        except Exception as feedback:
            logging.warning(u"Unable to remove participant '{}'".format(person))
            logging.exception(feedback)

    def post_message(self,
                     text=None,
                     content=None,
                     file=None,
                     space_id=None,
                     **kwargs):
        """
        Posts a message to a Cisco Spark room

        :param text: message in plain text
        :type text: str

        :param content: rich format, such as Markdown or HTML
        :type content: str

        :param file: URL or local path for an attachment
        :type file: str

        :param space_id: unique id of the target space
        :type space_id: str

        Example message out of plain text::

           space.post_message(text='hello world')

        Example message with Markdown::

           space.post_message(content='this is a **bold** statement')

        Example file upload::

           space.post_message(file='./my_file.pdf')

        Of course, you can combine text with the upload of a file::

           text = 'This is the presentation that was used for our meeting'
           space.post_message(text=text,
                              file='./my_file.pdf')

        If no space id is provided, then the function can use the unique id
        of this space, if one has been defined. Or an exception may be raised
        if no id has been made available.

        """

        logging.info(u"Posting message")
        if text not in (None, ''):
            logging.debug(u"- text: {}".format(
                text[:50] + (text[50:] and '..')))
        if content not in (None, ''):
            logging.debug(u"- content: {}".format(
                content[:50] + (content[50:] and '..')))
        if file not in (None, ''):
            logging.debug(u"- file: {}".format(
                file[:50] + (file[50:] and '..')))

        assert self.api is not None  # connect() is prerequisite

        count = 2
        while count:
            try:
                id = space_id if space_id else self.id
                files = [file] if file else None
                self.api.messages.create(roomId=id,
                                         text=text,
                                         markdown=content,
                                         files=files)
                logging.debug(u"- done")
                break

            except Exception as feedback:
                logging.warning(u"Unable to post message")
                time.sleep(0.1)
                count -= 1
                if count == 0:
                    logging.exception(feedback)

    def register(self, hook_url):
        """
        Connects in the background to Cisco Spark inbound events

        :param webhook: web address to be used by Cisco Spark service
        :type webhook: str

        This function registers the provided hook multiple times, so as to
        receive mutiple kind of updates:

        - The bot is invited to a room, or kicked out of it:
          webhook name = shellbot-rooms
          resource = memberships,
          event = all,
          personId = bot id,
          registered with bot token

        - Messages are sent, maybe with some files:
          webhook name = shellbot-messages
          resource = messages,
          event = created,
          registered with personal token (for chat auditing)

        - People are joining or leaving:
          webhook name = shellbot-participants
          resource = memberships,
          event = all,
          registered with personal token (for chat auditing)

        Previous webhooks registered with the bot token are all removed before
        registration. This means that only the most recent instance of the bot
        will be notified of new invitations.

        """
        assert hook_url not in (None, '')

        try:
            logging.debug(u"Purging bot webhooks")
            for webhook in self.api.webhooks.list():
#                logging.debug(u"- {}".format(str(webhook)))
                logging.debug(u"- deleting '{}'".format(webhook.name))
                self.api.webhooks.delete(webhookId=webhook.id)

            purged = ('shellbot-webhook',
                      'shellbot-messages',
                      'shellbot-participants')

            logging.debug(u"Purging personal webhooks")
            for webhook in self.personal_api.webhooks.list():
#                logging.debug(u"- {}".format(str(webhook)))
                if webhook.name in purged:
                    logging.debug(u"- deleting '{}'".format(webhook.name))
                    self.personal_api.webhooks.delete(webhookId=webhook.id)

        except Exception as feedback:
            logging.warning(u"Unable to handle webhook")
            logging.exception(feedback)

        logging.info(u"Registering webhook to Cisco Spark")
        logging.debug(u"- url: {}".format(hook_url))

        assert self.personal_api is not None  # connect() is prerequisite

        try:

            logging.debug(u"- registering 'shellbot-rooms'")
            self.api.webhooks.create(name='shellbot-rooms',
                                     targetUrl=hook_url,
                                     resource='memberships',
                                     event='all',
                                     filter='personId='+self.context.get('bot.id'))

            logging.debug(u"- registering 'shellbot-messages'")
            self.personal_api.webhooks.create(name='shellbot-messages',
                                              targetUrl=hook_url,
                                              resource='messages',
                                              event='created')

            logging.debug(u"- registering 'shellbot-participants'")
            self.personal_api.webhooks.create(name='shellbot-participants',
                                              targetUrl=hook_url,
                                              resource='memberships',
                                              event='all')

        except Exception as feedback:
            logging.warning(u"Unable to add webhook")
            logging.exception(feedback)

    def webhook(self, message_id=None):
        """
        Processes the flow of events from Cisco Spark

        :param message_id: if provided, do not invoke the request object

        Example message received from Cisco Spark::

            {
              "id" : "Y2lzY29zcGFyazovL3VzL01FU1NBR0UvOTJkYjNiZTAtNDNiZC0xMWU2LThhZTktZGQ1YjNkZmM1NjVk",
              "roomId" : "Y2lzY29zcGFyazovL3VzL1JPT00vYmJjZWIxYWQtNDNmMS0zYjU4LTkxNDctZjE0YmIwYzRkMTU0",
              "roomType" : "group",
              "toPersonId" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mMDZkNzFhNS0wODMzLTRmYTUtYTcyYS1jYzg5YjI1ZWVlMmX",
              "toPersonEmail" : "julie@example.com",
              "text" : "PROJECT UPDATE - A new project plan has been published on Box: http://box.com/s/lf5vj. The PM for this project is Mike C. and the Engineering Manager is Jane W.",
              "markdown" : "**PROJECT UPDATE** A new project plan has been published [on Box](http://box.com/s/lf5vj). The PM for this project is <@personEmail:mike@example.com> and the Engineering Manager is <@personEmail:jane@example.com>.",
              "files" : [ "http://www.example.com/images/media.png" ],
              "personId" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mNWIzNjE4Ny1jOGRkLTQ3MjctOGIyZi1mOWM0NDdmMjkwNDY",
              "personEmail" : "matt@example.com",
              "created" : "2015-10-18T14:26:16+00:00",
              "mentionedPeople" : [ "Y2lzY29zcGFyazovL3VzL1BFT1BMRS8yNDlmNzRkOS1kYjhhLTQzY2EtODk2Yi04NzllZDI0MGFjNTM", "Y2lzY29zcGFyazovL3VzL1BFT1BMRS83YWYyZjcyYy0xZDk1LTQxZjAtYTcxNi00MjlmZmNmYmM0ZDg" ]
            }

        This function is called from far far away, over the Internet,
        when message_id` is None. Or it is called locally, from test environment,
        when `message_id` has a value.
        """

        try:

            logging.debug(u'Receiving data from webhook')

            if message_id:
                resource = 'messages'
                event = 'created'
                hook = 'injection'

            else:
#                logging.debug(u"- {}".format(request.json))
                resource = request.json['resource']
                event = request.json['event']
                data = request.json['data']
                hook = request.json['name']

            if resource == 'messages' and event == 'created':
                logging.debug(u"- handling '{}:{}'".format(resource, event))

                if not message_id:
                    message_id = data['id']

                retries = 2
                while retries:
                    try:
                        item = self.personal_api.messages.get(messageId=message_id)
                        item._json['hook'] = hook
                        self.on_message(item._json, self.ears)
                        break
                    except Exception:
                        if retries:
                            retries -= 1
                            time.sleep(0.1)
                            continue
                        raise

            elif resource == 'memberships' and event == 'created':
                logging.debug(u"- handling '{}:{}'".format(resource, event))

                item = self.personal_api.rooms.get(roomId=data['roomId'])
#                logging.debug(u"- {}".format(item._json))

                data['space_title'] = item._json['title']
                data['space_type'] = item._json['type']
                data['hook'] = hook
#                logging.debug(u"- {}".format(data))

                self.on_join(data, self.ears)

            elif resource == 'memberships' and event == 'deleted':
                logging.debug(u"- handling '{}:{}'".format(resource, event))

                item = self.personal_api.rooms.get(roomId=data['roomId'])
#                logging.debug(u"- {}".format(item._json))

                data['space_title'] = item._json['title']
                data['space_type'] = item._json['type']
                data['hook'] = hook
#                logging.debug(u"- {}".format(data))

                self.on_leave(data, self.ears)

            else:
                logging.debug(u"- throwing away {}:{}".format(resource, event))
                logging.debug(u"- {}".format(data))

            return "OK"

        except Exception as feedback:
            logging.error(u"Unable to process webhook event")
            logging.error(feedback)
            raise

    def pull(self):
        """
        Fetches events from one Cisco Spark room

        This function senses most recent items, and pushes them
        to a processing queue.
        """

        assert self.is_ready

        logging.info(u'Pulling messages')
        self.context.increment(u'puller.counter')

        assert self.api is not None  # connect() is prerequisite
        new_items = []
        try:
            items = self.api.messages.list(roomId=self.id,
                                           mentionedPeople=['me'],
                                           max=10)

            for item in items:

                if item.id == self._last_message_id:
                    break

                new_items.append(item)

        except Exception as feedback:
            logging.warning(u"Unable to pull messages")
            logging.exception(feedback)
            return

        if len(new_items):
            logging.info(u"Pulling {} new messages".format(len(new_items)))

        while len(new_items):
            item = new_items.pop()
            self._last_message_id = item.id
            item._json['hook'] = 'pull'
            self.on_message(item._json, self.ears)

    def on_message(self, item, queue):
        """
        Normalizes message for the listener

        :param item: attributes of the inbound message
        :type item: dict

        :param queue: the processing queue
        :type queue: Queue

        This function prepares a Message and push it to the provided queue.

        This function adds following keys to messages so that a neutral format
        can be used with the listener:

        * ``type`` is set to ``message``
        * ``content`` is a copy of ``html``
        * ``from_id`` is a copy of ``personId``
        * ``from_label`` is a copy of ``personEmail``
        * ``mentioned_ids`` is a copy of ``mentionedPeople``

        """
        message = Message(item.copy())
        message.content = message.get('html', message.text)
        message.from_id = message.get('personId')
        message.from_label = message.get('personEmail')
        message.mentioned_ids = message.get('mentionedPeople', [])
        message.space_id = message.get('roomId')

        logging.debug(u"- putting message to ears")
        queue.put(str(message))

        for url in item.get('files', []):
            attachment = Attachment(item.copy())
            attachment.url = url
            attachment.from_id = item.get('personId', None)
            attachment.from_label = item.get('personEmail', None)
            attachment.space_id = item.get('roomId', None)

            logging.debug(u"- putting attachment to ears")
            queue.put(str(attachment))

    def download_attachment(self, url):
        """
        Copies a shared document locally
        """
        path = tempfile.gettempdir()+'/'+self.name_attachment(url)
        logging.debug(u"- writing to {}".format(path))
        with open(path, "w+b") as handle:
            handle.write(self.get_attachment(url))

        return path

    def name_attachment(self, url, response=None):
        """
        Retrieves a document attached to a room
        """
        logging.debug(u"- sensing {}".format(url))

        headers = {}
        if self.personal_token:
            headers['Authorization'] = 'Bearer '+self.personal_token
        elif self.token:
            headers['Authorization'] = 'Bearer '+self.token

        if not response:
            response = requests.head(url=url, headers=headers)

        logging.debug(u"- status: {}".format(response.status_code))
        if response.status_code != 200:
            raise Exception(u"Unable to download attachment")

        logging.debug(u"- headers: {}".format(response.headers))
        line = response.headers['Content-Disposition']
        match = re.search('filename=(.+)', line)
        if match:
            name = match.group(1).strip()
            if name.startswith('"') and name.endswith('"'):
                name = name[1:-1]
            return name

        return 'downloadable'

    def get_attachment(self, url, response=None):
        """
        Retrieves a document attached to a room
        """
        logging.debug(u"- fetching {}".format(url))

        headers = {}
        if self.personal_token:
            headers['Authorization'] = 'Bearer '+self.personal_token
        elif self.token:
            headers['Authorization'] = 'Bearer '+self.token

        if not response:
            response = requests.get(url=url, headers=headers)

        logging.debug(u"- status: {}".format(response.status_code))
        if response.status_code != 200:
            raise Exception(u"Unable to download attachment")

        logging.debug(u"- headers: {}".format(response.headers))
        logging.debug(u"- encoding: {}".format(response.encoding))
        logging.debug(u"- length: {}".format(len(response.content)))
        return response.content

    def on_join(self, item, queue):
        """
        Normalizes message for the listener

        :param item: attributes of the inbound message
        :type item: dict

        :param queue: the processing queue
        :type queue: Queue

        Example item received on memberships:create::

            {
                'isMonitor': False,
                'created': '2017-05-31T21:25:30.424Z',
                'personId': 'Y2lzY29zcGFyazovL3VRiMTAtODZkYy02YzU0Yjg5ODA5N2U',
                'isModerator': False,
                'personOrgId': 'Y2lzY29zcGFyazovL3V0FOSVpBVElPTi9jb25zdW1lcg',
                'personDisplayName': 'foo.bar@acme.com',
                'personEmail': 'foo.bar@acme.com',
                'roomId': 'Y2lzY29zcGFyazovL3VzL1JP3LTk5MDAtMDU5MDI2YjBiNDUz',
                'id': 'Y2lzY29zcGFyazovL3VzDctMTFlNy05OTAwLTA1OTAyNmIwYjQ1Mw'
            }

        This function prepares a Join and push it to the provided queue.

        * ``type`` is set to ``join``
        * ``actor_id`` is a copy of ``personId``
        * ``actor_address`` is a copy of ``personEmail``
        * ``actor_label`` is a copy of ``personDisplayName``

        """
        join = Join(item.copy())
        join.actor_id = join.get('personId')
        join.actor_address = join.get('personEmail')
        join.actor_label = join.get('personDisplayName')
        join.space_id = join.get('roomId')

        queue.put(str(join))

    def on_leave(self, item, queue):
        """
        Normalizes message for the listener

        :param item: attributes of the inbound message
        :type item: dict

        :param queue: the processing queue
        :type queue: Queue

        Example item received on memberships:delete::

            {
                'isMonitor': False,
                'created': '2017-05-31T21:25:30.424Z',
                'personId': 'Y2lzY29zcGFyazovL3VRiMTAtODZkYy02YzU0Yjg5ODA5N2U',
                'isModerator': False,
                'personOrgId': 'Y2lzY29zcGFyazovL3V0FOSVpBVElPTi9jb25zdW1lcg',
                'personDisplayName': 'foo.bar@acme.com',
                'personEmail': 'foo.bar@acme.com',
                'roomId': 'Y2lzY29zcGFyazovL3VzL1JP3LTk5MDAtMDU5MDI2YjBiNDUz',
                'id': 'Y2lzY29zcGFyazovL3VzDctMTFlNy05OTAwLTA1OTAyNmIwYjQ1Mw'
            }

        This function prepares a Leave and push it to the provided queue.

        * ``type`` is set to ``leave``
        * ``actor_id`` is a copy of ``personId``
        * ``actor_address`` is a copy of ``personEmail``
        * ``actor_label`` is a copy of ``personDisplayName``

        """
        leave = Leave(item.copy())
        leave.actor_id = leave.get('personId')
        leave.actor_address = leave.get('personEmail')
        leave.actor_label = leave.get('personDisplayName')
        leave.space_id = leave.get('roomId')

        queue.put(str(leave))

    def update_title(self, title):
        """
        Update the title of the space as requested

        :return: the configured title, or ``Collaboration space``
        :rtype: str

        This function should be rewritten in sub-classes if
        space title does not come from ``space.room`` parameter.
        """
        return self.api.room.update(self.id, title)


