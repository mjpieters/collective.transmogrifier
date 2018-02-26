# -*- coding: utf-8 -*-
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.transmogrifier import configuration_registry
from zope.testing import cleanup

import os
import shutil
import tempfile


# Doctest support

BASEDIR = None


def registerConfig(name, configuration):
    filename = os.path.join(BASEDIR, '%s.cfg' % name)
    open(filename, 'w').write(configuration)
    configuration_registry.registerConfiguration(
        name,
        u"Pipeline configuration '%s' from "
        u"'collective.transmogrifier.tests'" % name,
        u'', filename)


def setUp(test):
    global BASEDIR
    BASEDIR = tempfile.mkdtemp('transmogrifierTestConfigs')

    class PloneSite(object):

        def Title(self):
            return u'Plone Test Site'

        def getPhysicalPath(self):
            return ('', 'plone')

        def absolute_url(self):
            return 'http://nohost/plone'

    test.globs.update(dict(
        registerConfig=registerConfig,
        ISectionBlueprint=ISectionBlueprint,
        ISection=ISection,
        plone=PloneSite(),
    ))


def tearDown(test):
    shutil.rmtree(BASEDIR)
    cleanup.cleanUp()
