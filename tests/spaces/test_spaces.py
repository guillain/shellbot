#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import gc
import logging
import mock
import os
from multiprocessing import Process
import sys
import time

sys.path.insert(0, os.path.abspath('../..'))

from shellbot import Context
from shellbot.spaces import SpaceFactory


my_context = Context()

class SpaceFactoryTests(unittest.TestCase):

    def tearDown(self):
        my_context.clear()
        collected = gc.collect()
        logging.info("Garbage collector: collected %d objects." % (collected))

    def test_build_space(self):

        logging.info("***** build generic space from settings")

        my_context.apply(settings={  # from settings to member attributes
            'space': {
                'room': 'My preferred room',
                'moderators':
                    ['foo.bar@acme.com', 'joe.bar@corporation.com'],
                'participants':
                    ['alan.droit@azerty.org', 'bob.nard@support.tv'],
                'team': 'Anchor team',
                'token': 'hkNWEtMJNkODVGlZWU1NmYtyY',
                'personal_token': '*personal*secret*token',
                'webhook': "http://73a1e282.ngrok.io",
            }
        })

        space = SpaceFactory.build(context=my_context)
        self.assertEqual(space.id, None)   #  set after bond()
        self.assertEqual(space.title, None)

    def test_build_local(self):

        logging.info("***** build local space from settings")

        my_context.apply(settings={  # from settings to member attributes
            'local': {
                'room': 'My preferred room',
                'moderators':
                    ['foo.bar@acme.com', 'joe.bar@corporation.com'],
                'participants':
                    ['alan.droit@azerty.org', 'bob.nard@support.tv'],
                'input': ['help', 'version'],
            }
        })

        space = SpaceFactory.build(context=my_context)
        self.assertEqual(space.id, None)   #  set after bond()
        self.assertEqual(space.title, None)

    def test_build_spark(self):

        logging.info("***** build Cisco Spark space from settings")

        my_context.apply(settings={  # from settings to member attributes
            'spark': {
                'room': 'My preferred room',
                'moderators':
                    ['foo.bar@acme.com', 'joe.bar@corporation.com'],
                'participants':
                    ['alan.droit@azerty.org', 'bob.nard@support.tv'],
                'team': 'Anchor team',
                'token': 'hkNWEtMJNkODVGlZWU1NmYtyY',
                'personal_token': '*personal*secret*token',
                'webhook': "http://73a1e282.ngrok.io",
            }
        })

        space = SpaceFactory.build(context=my_context)
        self.assertEqual(space.token, 'hkNWEtMJNkODVGlZWU1NmYtyY')
        self.assertEqual(space.personal_token, '*personal*secret*token')
        self.assertEqual(space.id, None)   #  set after bond()
        self.assertEqual(space.title, None)
        self.assertEqual(space.teamId, None)

    def test_sense_space(self):

        logging.info("***** sense generic space")

        my_context.apply(settings={  # sense='space'
            'space': {
                'room': 'My preferred room',
                'moderators':
                    ['foo.bar@acme.com', 'joe.bar@corporation.com'],
                'participants':
                    ['alan.droit@azerty.org', 'bob.nard@support.tv'],
                'team': 'Anchor team',
                'token': 'hkNWEtMJNkODk3ZDZLOGQ0OVGlZWU1NmYtyY',
                'personal_token': '$MY_FUZZY_SPARK_TOKEN',
                'fuzzy_token': '$MY_FUZZY_SPARK_TOKEN',
                'webhook': "http://73a1e282.ngrok.io",
            }
        })

        self.assertEqual(SpaceFactory.sense(my_context), 'space')

    def test_sense_local(self):

        logging.info("***** sense local space")

        my_context.apply(settings={  # sense='local'
            'local': {
                'room': 'My preferred room',
                'moderators':
                    ['foo.bar@acme.com', 'joe.bar@corporation.com'],
                'participants':
                    ['alan.droit@azerty.org', 'bob.nard@support.tv'],
                'input': ['help', 'version'],
            }
        })

        self.assertEqual(SpaceFactory.sense(my_context), 'local')

    def test_sense_spark(self):

        logging.info("***** sense Cisco Spark space")

        my_context.apply(settings={  # sense='spark'
            'spark': {
                'room': 'My preferred room',
                'moderators':
                    ['foo.bar@acme.com', 'joe.bar@corporation.com'],
                'participants':
                    ['alan.droit@azerty.org', 'bob.nard@support.tv'],
                'team': 'Anchor team',
                'token': 'hkNWEtMJNkODk3ZDZLOGQ0OVGlZWU1NmYtyY',
                'personal_token': '$MY_FUZZY_SPARK_TOKEN',
                'fuzzy_token': '$MY_FUZZY_SPARK_TOKEN',
                'webhook': "http://73a1e282.ngrok.io",
            }
        })

        self.assertEqual(SpaceFactory.sense(my_context), 'spark')

    def test_sense_alphabetical(self):

        logging.info("***** sense first space in alphabetical order")

        my_context.apply(settings={  # 'space' is coming before 'spark'
            'spark': {
                'room': 'My preferred room',
                'moderators':
                    ['foo.bar@acme.com', 'joe.bar@corporation.com'],
                'participants':
                    ['alan.droit@azerty.org', 'bob.nard@support.tv'],
                'team': 'Anchor team',
                'token': 'hkNWEtMJNkODk3ZDZLOGQ0OVGlZWU1NmYtyY',
                'personal_token': '$MY_FUZZY_SPARK_TOKEN',
                'fuzzy_token': '$MY_FUZZY_SPARK_TOKEN',
                'webhook': "http://73a1e282.ngrok.io",
            },

            'space': {
                'room': 'My preferred room',
                'moderators':
                    ['foo.bar@acme.com', 'joe.bar@corporation.com'],
                'participants':
                    ['alan.droit@azerty.org', 'bob.nard@support.tv'],
                'team': 'Anchor team',
                'token': 'hkNWEtMJNkODk3ZDZLOGQ0OVGlZWU1NmYtyY',
                'personal_token': '$MY_FUZZY_SPARK_TOKEN',
                'fuzzy_token': '$MY_FUZZY_SPARK_TOKEN',
                'webhook': "http://73a1e282.ngrok.io",
            },
        })

        self.assertEqual(SpaceFactory.sense(my_context), 'space')

        my_context.apply(settings={  # 'space' is coming before 'spark'
            'space': {
                'room': 'My preferred room',
                'moderators':
                    ['foo.bar@acme.com', 'joe.bar@corporation.com'],
                'participants':
                    ['alan.droit@azerty.org', 'bob.nard@support.tv'],
                'team': 'Anchor team',
                'token': 'hkNWEtMJNkODk3ZDZLOGQ0OVGlZWU1NmYtyY',
                'personal_token': '$MY_FUZZY_SPARK_TOKEN',
                'fuzzy_token': '$MY_FUZZY_SPARK_TOKEN',
                'webhook': "http://73a1e282.ngrok.io",
            },

            'spark': {
                'room': 'My preferred room',
                'moderators':
                    ['foo.bar@acme.com', 'joe.bar@corporation.com'],
                'participants':
                    ['alan.droit@azerty.org', 'bob.nard@support.tv'],
                'team': 'Anchor team',
                'token': 'hkNWEtMJNkODk3ZDZLOGQ0OVGlZWU1NmYtyY',
                'personal_token': '$MY_FUZZY_SPARK_TOKEN',
                'fuzzy_token': '$MY_FUZZY_SPARK_TOKEN',
                'webhook': "http://73a1e282.ngrok.io",
            },
        })

        self.assertEqual(SpaceFactory.sense(my_context), 'space')

    def test_sense_void(self):

        logging.info("***** sense nothing on bad configuration")

        my_context.apply(settings={  # no recognizable space type
            'not_a_space_type': {
                'room': 'My preferred room',
                'moderators':
                    ['foo.bar@acme.com', 'joe.bar@corporation.com'],
                'participants':
                    ['alan.droit@azerty.org', 'bob.nard@support.tv'],
                'team': 'Anchor team',
                'token': 'hkNWEtMJNkODk3ZDZLOGQ0OVGlZWU1NmYtyY',
                'personal_token': '$MY_FUZZY_SPARK_TOKEN',
                'fuzzy_token': '$MY_FUZZY_SPARK_TOKEN',
                'webhook': "http://73a1e282.ngrok.io",
            },

            'neither_me': {
                'room': 'My preferred room',
                'moderators':
                    ['foo.bar@acme.com', 'joe.bar@corporation.com'],
                'participants':
                    ['alan.droit@azerty.org', 'bob.nard@support.tv'],
                'team': 'Anchor team',
                'token': 'hkNWEtMJNkODk3ZDZLOGQ0OVGlZWU1NmYtyY',
                'personal_token': '$MY_FUZZY_SPARK_TOKEN',
                'fuzzy_token': '$MY_FUZZY_SPARK_TOKEN',
                'webhook': "http://73a1e282.ngrok.io",
            },
        })

        with self.assertRaises(ValueError):
            SpaceFactory.sense(my_context)

    def test_get_space(self):

        logging.info("***** get generic space")

        space = SpaceFactory.get(type='space')
        self.assertEqual(space.prefix, 'space')
        self.assertEqual(space.id, None)
        self.assertEqual(space.title, None)

        space = SpaceFactory.get(type='space', context='c', weird='w')
        self.assertEqual(space.context, 'c')
        with self.assertRaises(AttributeError):
            self.assertEqual(space.weird, 'w')
        self.assertEqual(space.prefix, 'space')
        self.assertEqual(space.id, None)
        self.assertEqual(space.title, None)

    def test_get_local(self):

        logging.info("***** get local space")

        space = SpaceFactory.get(type='local', input=['hello', 'world'])
        self.assertEqual(space.prefix, 'local')
        self.assertEqual(space.id, None)
        self.assertEqual(space.title, None)
        self.assertEqual(space.moderators, [])
        self.assertEqual(space.participants, [])

    def test_get_spark(self):

        logging.info("***** get Cisco Spark space")

        space = SpaceFactory.get(type='spark', context=my_context, token='b')
        self.assertEqual(space.token, 'b')
        self.assertEqual(space.id, None)
        self.assertEqual(space.title, None)
        self.assertEqual(space.teamId, None)

    def test_get_unknown(self):

        logging.info("***** get invalid space")

        with self.assertRaises(ValueError):
            space = SpaceFactory.get(type='*unknown', ex_token='b', ex_ears='c')

if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
