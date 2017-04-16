#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import logging
from mock import MagicMock
import os
import mock
from multiprocessing import Process, Queue
import random
import sys
import time
from webtest import TestApp

sys.path.insert(0, os.path.abspath('..'))

from shellbot import Context, Server
from shellbot.routes import Route, Static, Notify, Wrapper


class ServerTests(unittest.TestCase):

    def test_init(self):

        logging.info('*** Init test ***')

        server = Server()
        self.assertTrue(server.context is not None)
        self.assertTrue(server.httpd is not None)

        context = Context()
        server = Server(context=context, httpd='h')
        self.assertEqual(server.context, context)
        self.assertEqual(server.httpd, 'h')

    def test_configuration(self):

        logging.info('*** Configuration test ***')

        server = Server()

        server.configure({
            'server': {
                'address': '1.2.3.4',
                'port': 8888,
                'debug': True,
            },
        })
        self.assertEqual(server.context.get('server.address'), '1.2.3.4')
        self.assertEqual(server.context.get('server.port'), 8888)
        self.assertEqual(server.context.get('server.debug'), True)

    def test_routes(self):

        logging.info('*** Routes test ***')

        hello = Route(route='/hello')
        world = Route(route='/world')

        server = Server()
        server.load_routes([hello, world])
        self.assertEqual(server.routes, ['/hello', '/world'])
        self.assertEqual(server.route('/hello'), hello)
        self.assertEqual(server.route('/world'), world)

        server = Server(routes=[hello, world])
        self.assertEqual(server.routes, ['/hello', '/world'])
        self.assertEqual(server.route('/hello'), hello)
        self.assertEqual(server.route('/world'), world)

    def test_route(self):

        logging.info('*** Route test ***')

        route = Route(route='/hello')

        server = Server()
        server.load_route(route)
        self.assertEqual(server.routes, ['/hello'])
        self.assertEqual(server.route('/hello'), route)

        server = Server(route=route)
        self.assertEqual(server.routes, ['/hello'])
        self.assertEqual(server.route('/hello'), route)

    def test_run(self):

        logging.info('*** Run test ***')

        class FakeHttpd(object):
            def run(self, **kwargs):
                pass

        server = Server(httpd=FakeHttpd())
        server.run()

    def test_static(self):

        logging.info('*** Static test***')

        route = Static(route='/hello', page='Hello, world!')

        server = Server()
        server.load_route(route)

        test = TestApp(server.httpd)
        r = test.get('/hello')
        self.assertEqual(r.status, '200 OK')
        r.mustcontain('Hello, world!')

    def test_notify(self):

        logging.info('*** Notify test***')

        queue = Queue()
        route = Notify(route='/notify', queue=queue, notification='hello!')

        server = Server()
        server.load_route(route)

        test = TestApp(server.httpd)
        r = test.get('/notify')
        self.assertEqual(r.status, '200 OK')
        r.mustcontain('OK')
        time.sleep(0.1)
        self.assertEqual(queue.get_nowait(), 'hello!')

    def test_wrapper(self):

        logging.info('*** Wrapper test***')

        context = Context()

        class Callable(object):
            def __init__(self, context):
                self.context = context

            def hook(self, **kwargs):
                self.context.set('signal', 'wrapped!')
                return 'OK'

        callable = Callable(context)

        route = Wrapper(context=context,
                        route='/wrapper',
                        callable=callable.hook)

        server = Server(context=context)
        server.load_route(route)

        self.assertEqual(context.get('signal'), None)

        test = TestApp(server.httpd)
        r = test.get('/wrapper')
        self.assertEqual(r.status, '200 OK')
        r.mustcontain('OK')

        self.assertEqual(context.get('signal'), 'wrapped!')


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())