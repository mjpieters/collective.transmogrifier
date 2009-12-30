import os
import shutil
import tempfile
from zope.testing import cleanup

from collective.transmogrifier.transmogrifier import configuration_registry
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.interfaces import ISection

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
    
    test.globs.update(dict(
        registerConfig=registerConfig,
        ISectionBlueprint=ISectionBlueprint,
        ISection=ISection,
        plone=PloneSite(),
        ))

def tearDown(test):
    from collective.transmogrifier import transmogrifier
    shutil.rmtree(BASEDIR)
    cleanup.cleanUp()
