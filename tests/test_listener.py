#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import logging
import mock
import os
import sys
from multiprocessing import Process, Queue

sys.path.insert(0, os.path.abspath('..'))

from shellbot import Context, ShellBot, Listener


my_bot = ShellBot(ears=Queue(), mouth=Queue())
my_bot.shell.load_default_commands()

class ListenerTests(unittest.TestCase):

    def test_static(self):

        logging.info('*** Static test ***')

        listener = Listener(bot=my_bot)

        listener_process = Process(target=listener.work)
        listener_process.daemon = True
        listener_process.start()

        listener_process.join(0.1)
        if listener_process.is_alive():
            logging.info('Stopping listener')
            my_bot.context.set('general.switch', 'off')
            listener_process.join()

        self.assertFalse(listener_process.is_alive())
        self.assertEqual(my_bot.context.get('listener.counter', 0), 0)

    def test_dynamic(self):

        logging.info('*** Dynamic test ***')

        items = [

            {
              "id" : "1_lzY29zcGFyazovL3VzL01FU1NBR0UvOTJkYjNiZTAtNDNiZC0xMWU2LThhZTktZGQ1YjNkZmM1NjVk",
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
            },

            {
              "id" : "2_2lzY29zcGFyazovL3VzL01FU1NBR0UvOTJkYjNiZTAtNDNiZC0xMWU2LThhZTktZGQ1YjNkZmM1NjVk",
              "roomId" : "Y2lzY29zcGFyazovL3VzL1JPT00vYmJjZWIxYWQtNDNmMS0zYjU4LTkxNDctZjE0YmIwYzRkMTU0",
              "roomType" : "group",
              "toPersonId" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mMDZkNzFhNS0wODMzLTRmYTUtYTcyYS1jYzg5YjI1ZWVlMmX",
              "toPersonEmail" : "julie@example.com",
              "text" : "/shelly version",
              "personId" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mNWIzNjE4Ny1jOGRkLTQ3MjctOGIyZi1mOWM0NDdmMjkwNDY",
              "personEmail" : "matt@example.com",
              "created" : "2015-10-18T14:26:16+00:00",
              "mentionedPeople" : [ "Y2lzY29zcGFyazovL3VzL1BFT1BMRS8yNDlmNzRkOS1kYjhhLTQzY2EtODk2Yi04NzllZDI0MGFjNTM", "Y2lzY29zcGFyazovL3VzL1BFT1BMRS83YWYyZjcyYy0xZDk1LTQxZjAtYTcxNi00MjlmZmNmYmM0ZDg" ]
            },

            {
              "id" : "3_2lzY29zcGFyazovL3VzL01FU1NBR0UvOTJkYjNiZTAtNDNiZC0xMWU2LThhZTktZGQ1YjNkZmM1NjVk",
              "roomId" : "Y2lzY29zcGFyazovL3VzL1JPT00vYmJjZWIxYWQtNDNmMS0zYjU4LTkxNDctZjE0YmIwYzRkMTU0",
              "roomType" : "group",
              "toPersonId" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mMDZkNzFhNS0wODMzLTRmYTUtYTcyYS1jYzg5YjI1ZWVlMmX",
              "toPersonEmail" : "julie@example.com",
              "text" : "/shelly help",
              "personId" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mNWIzNjE4Ny1jOGRkLTQ3MjctOGIyZi1mOWM0NDdmMjkwNDY",
              "personEmail" : "matt@example.com",
              "created" : "2015-10-18T14:26:16+00:00",
              "mentionedPeople" : [ "Y2lzY29zcGFyazovL3VzL1BFT1BMRS8yNDlmNzRkOS1kYjhhLTQzY2EtODk2Yi04NzllZDI0MGFjNTM", "Y2lzY29zcGFyazovL3VzL1BFT1BMRS83YWYyZjcyYy0xZDk1LTQxZjAtYTcxNi00MjlmZmNmYmM0ZDg" ]
            },

            {
              "id" : "3_2lzY29zcGFyazovL3VzL01FU1NBR0UvOTJkYjNiZTAtNDNiZC0xMWU2LThhZTktZGQ1YjNkZmM1NjVk",
              "roomId" : "Y2lzY29zcGFyazovL3VzL1JPT00vYmJjZWIxYWQtNDNmMS0zYjU4LTkxNDctZjE0YmIwYzRkMTU0",
              "roomType" : "group",
              "toPersonId" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mMDZkNzFhNS0wODMzLTRmYTUtYTcyYS1jYzg5YjI1ZWVlMmX",
              "toPersonEmail" : "julie@example.com",
              "text" : "/shelly help help",
              "personId" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mNWIzNjE4Ny1jOGRkLTQ3MjctOGIyZi1mOWM0NDdmMjkwNDY",
              "personEmail" : "matt@example.com",
              "created" : "2015-10-18T14:26:16+00:00",
              "mentionedPeople" : [ "Y2lzY29zcGFyazovL3VzL1BFT1BMRS8yNDlmNzRkOS1kYjhhLTQzY2EtODk2Yi04NzllZDI0MGFjNTM", "Y2lzY29zcGFyazovL3VzL1BFT1BMRS83YWYyZjcyYy0xZDk1LTQxZjAtYTcxNi00MjlmZmNmYmM0ZDg" ]
            },

            {
              "id" : "4_2lzY29zcGFyazovL3VzL01FU1NBR0UvOTJkYjNiZTAtNDNiZC0xMWU2LThhZTktZGQ1YjNkZmM1NjVk",
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
            },

        ]

        for item in items:
            my_bot.ears.put(item)

        my_bot.ears.put(Exception('EOQ'))

        tee = Queue()
        listener = Listener(bot=my_bot, tee=tee)

        listener.work()

        self.assertEqual(my_bot.context.get('listener.counter'), 5)
        with self.assertRaises(Exception):
            my_bot.ears.get_nowait()
        with self.assertRaises(Exception):
            my_bot.inbox.get_nowait()
        self.assertEqual(my_bot.mouth.get(), 'Shelly version *unknown*')
        self.assertEqual(
            my_bot.mouth.get(),
            u'Available commands:\n'
            + u'echo - Echo input string.\nhelp - Show commands and usage.')
        self.assertEqual(
            my_bot.mouth.get(),
            u'help - Show commands and usage.\nusage:\nhelp <command>')
        with self.assertRaises(Exception):
            print(my_bot.mouth.get_nowait())

        for item in items:
            self.assertEqual(tee.get(), item)
        with self.assertRaises(Exception):
            print(tee.get_nowait())

    def test_work(self):

        logging.info("*** work")

        my_bot.context = Context()
        listener = Listener(bot=my_bot)
        listener.process = mock.Mock(side_effect=Exception('unexpected exception'))
        listener.ears.put(('dummy'))
        listener.work()
        self.assertEqual(listener.context.get('listener.counter'), 1)

        my_bot.context = Context()
        listener = Listener(bot=my_bot)
        listener.process = mock.Mock(side_effect=KeyboardInterrupt('ctl-C'))
        listener.ears.put(('dummy'))
        listener.work()
        self.assertEqual(listener.context.get('listener.counter'), 1)

if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
