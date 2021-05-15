# -*- coding: utf-8 -*-
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.interfaces import ITransmogrifier
from collective.transmogrifier.tests import setUp
from collective.transmogrifier.tests import tearDown
from collective.transmogrifier.transmogrifier import configuration_registry
from zope.component import provideAdapter
from zope.component import provideUtility
from zope.interface import classImplements
from zope.interface import directlyProvides
from zope.interface import implementer
from zope.testing import cleanup
from Zope2.App import zcml

import collective.transmogrifier
import doctest
import operator
import os
import shutil
import tempfile
import unittest


# Unit tests

class MetaDirectivesTests(unittest.TestCase):

    def setUp(self):
        zcml.load_config('meta.zcml', collective.transmogrifier)

    def tearDown(self):
        configuration_registry.clear()
        cleanup.cleanUp()

    def testEmptyZCML(self):
        zcml.load_string('''\
<configure xmlns:transmogrifier="http://namespaces.plone.org/transmogrifier">
</configure>''')
        self.assertEqual(configuration_registry.listConfigurationIds(), ())

    def testConfigZCML(self):
        zcml.load_string('''\
<configure
    xmlns:transmogrifier="http://namespaces.plone.org/transmogrifier"
    i18n_domain="collective.transmogrifier">
<transmogrifier:registerConfig
    name="collective_transmogrifier_tests_configname"
    title="config title"
    description="config description"
    configuration="filename.cfg"
    />
</configure>''')
        self.assertEqual(configuration_registry.listConfigurationIds(),
                         (u'collective_transmogrifier_tests_configname',))
        path = os.path.split(collective.transmogrifier.__file__)[0]
        self.assertEqual(
            configuration_registry.getConfiguration(
                u'collective_transmogrifier_tests_configname'),
            dict(id=u'collective_transmogrifier_tests_configname',
                 title=u'config title',
                 description=u'config description',
                 configuration=os.path.join(path, 'filename.cfg')))

    def testConfigZCMLDefaults(self):
        zcml.load_string('''\
<configure
    xmlns:transmogrifier="http://namespaces.plone.org/transmogrifier"
    i18n_domain="collective.transmogrifier">
<transmogrifier:registerConfig
    name="collective_transmogrifier_tests_configname"
    configuration="filename.cfg"
    />
</configure>''')
        self.assertEqual(configuration_registry.listConfigurationIds(),
                         (u'collective_transmogrifier_tests_configname',))
        path = os.path.split(collective.transmogrifier.__file__)[0]
        self.assertEqual(
            configuration_registry.getConfiguration(
                u'collective_transmogrifier_tests_configname'),
            dict(id=u'collective_transmogrifier_tests_configname',
                 title=u'Pipeline configuration '
                       u"'collective_transmogrifier_tests_configname'",
                 description=u'',
                 configuration=os.path.join(path, 'filename.cfg')))


class OptionSubstitutionTests(unittest.TestCase):

    def _loadOptions(self, opts):
        from collective.transmogrifier.transmogrifier import Transmogrifier
        tm = Transmogrifier(object())
        tm._raw = opts
        tm._data = {}
        return tm

    def testNoSubs(self):
        opts = self._loadOptions(
            dict(
                spam=dict(monty='python'),
                eggs=dict(foo='bar'),
            ))
        self.assertEqual(opts['spam']['monty'], 'python')
        self.assertEqual(opts['eggs']['foo'], 'bar')

    def testSimpleSub(self):
        opts = self._loadOptions(
            dict(
                spam=dict(monty='python'),
                eggs=dict(foo='${spam:monty}'),
            ))
        self.assertEqual(opts['spam']['monty'], 'python')
        self.assertEqual(opts['eggs']['foo'], 'python')

    def testSkipTALESStringExpressions(self):
        opts = self._loadOptions(
            dict(
                spam=dict(monty='string:${spam/eggs}'),
                eggs=dict(foo='${spam/monty}')
            ))
        self.assertEqual(opts['spam']['monty'], 'string:${spam/eggs}')
        self.assertRaises(ValueError, operator.itemgetter('eggs'), opts)

    def testErrors(self):
        opts = self._loadOptions(
            dict(
                empty=dict(),
                spam=dict(monty='${eggs:foo}'),
                eggs=dict(foo='${spam:monty}'),
            ))
        self.assertRaises(ValueError, operator.itemgetter('spam'), opts)
        self.assertRaises(KeyError, operator.itemgetter('dontexist'), opts)
        self.assertRaises(KeyError, operator.itemgetter('dontexist'),
                          opts['empty'])


class InclusionManipulationTests(cleanup.CleanUp, unittest.TestCase):

    def setUp(self):
        super(InclusionManipulationTests, self).setUp()
        self._basedir = tempfile.mkdtemp('transmogrifierTestConfigs')
        self._registerConfig(
            u'collective.transmogrifier.tests.included',
            '''\
[foo]
bar=
    monty
    python
''')

    def tearDown(self):
        super(InclusionManipulationTests, self).tearDown()
        shutil.rmtree(self._basedir)

    def _registerConfig(self, name, configuration):
        filename = os.path.join(self._basedir, '%s.cfg' % name)
        open(filename, 'w').write(configuration)
        configuration_registry.registerConfiguration(
            name,
            u"Pipeline configuration '%s' from "
            u"'collective.transmogrifier.tests'" % name,
            u'', filename)

    def _loadConfig(self, config):
        from collective.transmogrifier.transmogrifier import _load_config
        config = (
            '[transmogrifier]\n'
            'include=collective.transmogrifier.tests.included\n\n'
        ) + config
        self._registerConfig(
            u'collective.transmogrifier.tests.includer', config)
        return _load_config(u'collective.transmogrifier.tests.includer')

    def testAdd(self):
        opts = self._loadConfig('[foo]\nbar+=eggs\n')
        self.assertEquals(opts['foo']['bar'], 'monty\npython\neggs')

    def testRemove(self):
        opts = self._loadConfig('[foo]\nbar-=python\n')
        self.assertEquals(opts['foo']['bar'], 'monty')

    def testAddAndRemove(self):
        opts = self._loadConfig('''\
[foo]
bar -=
    monty
bar +=
    monty
    eggs
''')
        self.assertEquals(opts['foo']['bar'], 'python\nmonty\neggs')

    def testNonExistent(self):
        opts = self._loadConfig('[bar]\nfoo+=spam\nbaz-=monty\n')
        self.assertEquals(opts['bar']['foo'], 'spam')
        self.assertEquals(opts['bar']['baz'], '')


class ConstructPipelineTests(cleanup.CleanUp, unittest.TestCase):

    def _doConstruct(self, transmogrifier, sections, pipeline=None):
        from collective.transmogrifier.utils import constructPipeline
        return constructPipeline(transmogrifier, sections, pipeline)

    def testNoISection(self):
        config = dict(
            noisection=dict(
                blueprint='collective.transmogrifier.tests.noisection'))

        class NotAnISection(object):

            def __init__(self, transmogrifier, name, options, previous):
                self.previous = previous

            def __iter__(self):
                for item in self.previous:
                    yield item

        provideUtility(NotAnISection, ISectionBlueprint,
                       name=u'collective.transmogrifier.tests.noisection')
        self.assertRaises(ValueError, self._doConstruct,
                          config, ['noisection'])

        classImplements(NotAnISection, ISection)
        # No longer raises
        self._doConstruct(config, ['noisection'])


class DefaultKeysTest(unittest.TestCase):

    def _defaultKeys(self, *args):
        from collective.transmogrifier.utils import defaultKeys
        return defaultKeys(*args)

    def testWithKey(self):
        self.assertEqual(
            self._defaultKeys('foo.bar.baz', 'spam', 'eggs'),
            ('_foo.bar.baz_spam_eggs', '_foo.bar.baz_eggs',
             '_spam_eggs', '_eggs'))

    def testWithoutKey(self):
        self.assertEqual(
            self._defaultKeys('foo.bar.baz', 'spam'),
            ('_foo.bar.baz_spam', '_foo.bar.baz', '_spam'))


class PackageReferenceResolverTest(unittest.TestCase):

    def setUp(self):
        self._package_path = os.path.dirname(__file__)[:-len('/tests')]

    def _resolvePackageReference(self, ref):
        from collective.transmogrifier.utils import resolvePackageReference
        return resolvePackageReference(ref)

    def testPackageResolver(self):
        res = self._resolvePackageReference('collective.transmogrifier:test')
        self.assertEqual(res, os.path.join(self._package_path, 'test'))

    def testNonexistingPackage(self):
        self.assertRaises(ImportError, self._resolvePackageReference,
                          'collective.transmogrifier.nonexistent:test')


@implementer(ITransmogrifier)
class MockImportContext(object):

    def __init__(self, configfile=None):
        self.configfile = configfile

    def readDataFile(self, filename):
        assert filename == 'transmogrifier.txt'
        return self.configfile

    def getSite(self):
        return self

    def getLogger(self, name):
        assert name == 'collective.transmogrifier.genericsetup'
        return self

    log = ()

    def info(self, msg):
        self.log += (msg,)

    run = ()

    def __call__(self, config):
        from zope.annotation.interfaces import IAnnotations
        from collective.transmogrifier.genericsetup import IMPORT_CONTEXT
        assert IAnnotations(self)[IMPORT_CONTEXT] is self
        self.run += (config,)


class GenericSetupImporterTest(unittest.TestCase):

    def setUp(self):
        from zope.annotation.attribute import AttributeAnnotations
        provideAdapter(AttributeAnnotations)

    def tearDown(self):
        cleanup.cleanUp()

    def runOne(self, configfile=None):
        from collective.transmogrifier.genericsetup import importTransmogrifier
        from zope.annotation.interfaces import IAttributeAnnotatable
        context = MockImportContext(configfile)
        directlyProvides(context, IAttributeAnnotatable)
        importTransmogrifier(context)
        return context

    def testNoDataFile(self):
        context = self.runOne()
        self.assertEqual(context.log, ())
        self.assertEqual(context.run, ())

    def testEmptyDataFile(self):
        context = self.runOne('')
        self.assertEqual(context.log, ())
        self.assertEqual(context.run, ())

    def testOneConfigDataFile(self):
        context = self.runOne('foo.bar')
        self.assertEqual(context.log, (
            'Running transmogrifier pipeline foo.bar',
            'Transmogrifier pipeline foo.bar complete',
        ))
        self.assertEqual(context.run, ('foo.bar',))

    def testMultiConfigDataFile(self):
        context = self.runOne('foo.bar\n  # ignored\nspam.eggs\n')
        self.assertEqual(context.log, (
            'Running transmogrifier pipeline foo.bar',
            'Transmogrifier pipeline foo.bar complete',
            'Running transmogrifier pipeline spam.eggs',
            'Transmogrifier pipeline spam.eggs complete',
        ))
        self.assertEqual(context.run, ('foo.bar', 'spam.eggs'))


def test_suite():
    import sys
    suite = unittest.findTestCases(sys.modules[__name__])
    suite.addTests((
        doctest.DocFileSuite(
            '../../../../docs/source/transmogrifier.rst',
            setUp=setUp, tearDown=tearDown,
            optionflags=doctest.NORMALIZE_WHITESPACE),
    ))
    return suite
