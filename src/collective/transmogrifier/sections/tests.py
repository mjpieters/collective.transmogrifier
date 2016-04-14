import sys
import io
import itertools
import unittest
import mimetools
import urllib2
import shutil
import posixpath
from zope.component import provideUtility
from zope.interface import classProvides, implements
from zope.testing import doctest
from collective.transmogrifier.interfaces import ISectionBlueprint, ISection
from collective.transmogrifier.tests import setUp, tearDown
from Products.Five import zcml

_marker = object()


class SplitterConditionSectionTests(unittest.TestCase):
    def _makeOne(self, previous, condition=None):
        from splitter import SplitterConditionSection
        return SplitterConditionSection(condition, previous)

    def testIterates(self):
        section = self._makeOne(iter(range(10)))
        self.assertEqual(range(10), list(section))

    def testCondition(self):
        section = self._makeOne(iter(range(10)), lambda x: x % 2)
        self.assertEqual(range(1, 10, 2), list(section))

    def testAhead(self):
        section = self._makeOne(iter(range(3)))

        self.assertEqual(section.ahead, 0)
        self.assertFalse(section.isAhead)

        section.next()
        self.assertEqual(section.ahead, 1)
        self.assertTrue(section.isAhead)
        self.assertEqual(section.ahead, 0)
        self.assertFalse(section.isAhead)

        section.next()
        section.next()
        self.assertEqual(section.ahead, 2)
        self.assertTrue(section.isAhead)
        self.assertEqual(section.ahead, 1)
        self.assertTrue(section.isAhead)
        self.assertEqual(section.ahead, 0)
        self.assertFalse(section.isAhead)

        self.assertRaises(StopIteration, section.next)
        self.assertEqual(section.ahead, 1)
        self.assertTrue(section.isAhead)
        self.assertEqual(section.ahead, 0)
        self.assertFalse(section.isAhead)

    def testWillMatch(self):
        section = self._makeOne(iter(range(2)), lambda x: x % 2)

        self.assertFalse(section.willMatch)
        self.assertTrue(section.willMatch)
        self.assertEquals(section.next(), 1)
        self.assertFalse(section.willMatch)
        self.assertRaises(StopIteration, section.next)

        section = self._makeOne(iter(range(3)), lambda x: x < 1)
        self.assertTrue(section.willMatch)
        self.assertTrue(section.willMatch)
        self.assertEquals(section.next(), 0)
        self.assertFalse(section.willMatch)
        self.assertRaises(StopIteration, section.next)

    def testIsDone(self):
        section = self._makeOne(iter(range(1)))

        self.assertFalse(section.isDone)
        section.next()
        self.assertTrue(section.isDone)
        self.assertRaises(StopIteration, section.next)

    def testCopy(self):
        orig, source = itertools.tee((dict(foo=i) for i in range(2)), 2)
        section = self._makeOne(source)
        for original, yielded in itertools.izip(orig, section):
            self.assertEqual(original, yielded)
            self.assertFalse(original is yielded)


class SplitterSectionTests(unittest.TestCase):
    def _makeOne(self, transmogrifier, options, previous):
        from splitter import SplitterSection
        return SplitterSection(transmogrifier, 'unittest', options, previous)

    def testAtLeastTwo(self):
        self.assertRaises(ValueError, self._makeOne, {}, {}, iter(()))
        self.assertRaises(ValueError, self._makeOne, {}, {'pipeline-1': ''},
                          iter(()))
        # Shouldn't raise
        self._makeOne({}, {'pipeline-1': '', 'pipeline-2': ''}, iter(()))

    def testInsertExtra(self):
        class Inserter(object):
            implements(ISection)

            def __init__(self, transmogrifier, name, options, previous):
                self.previous = previous

            def __iter__(self):
                count = 0
                for item in self.previous:
                    item['pipeline'] = 1
                    yield item
                    yield dict(id='extra-%02d' % count)
                    count += 1

        provideUtility(Inserter, ISectionBlueprint,
            name=u'collective.transmogrifier.tests.inserter')
        splitter = self._makeOne(dict(
            inserter=dict(
                blueprint='collective.transmogrifier.tests.inserter')),
            {'pipeline-1': 'inserter', 'pipeline-2': ''},
            (dict(id='item-%02d' % i) for i in range(3)))
        self.assertEqual(list(splitter), [
            dict(id='item-00', pipeline=1), # p1 advanced, look at p2
            dict(id='item-00'),             # p2 advanced, look at p1
            dict(id='extra-00'),            # p1 did not advance
            dict(id='item-01', pipeline=1), # p1 advanced, look at p2
            dict(id='item-01'),             # p2 advanced, look at p1
            dict(id='extra-01'),            # p1 did not advance
            dict(id='item-02', pipeline=1), # p1 advanced, condition isDone
            dict(id='extra-02'),            # last in p1 after isDone, l.a. p2
            dict(id='item-02'),             # p2 advanced
        ])                                  # p2 is done

    def testSkipItems(self):
        class Skip(object):
            implements(ISection)

            def __init__(self, transmogrifier, name, options, previous):
                self.previous = previous

            def __iter__(self):
                count = 0
                for item in self.previous:
                    if count % 2:
                        item['pipeline'] = 1
                        yield item
                    count += 1
        provideUtility(Skip, ISectionBlueprint,
            name=u'collective.transmogrifier.tests.skip')
        splitter = self._makeOne(dict(
            skip=dict(
                blueprint='collective.transmogrifier.tests.skip')),
            {'pipeline-1': 'skip', 'pipeline-2': ''},
            (dict(id='item-%02d' % i) for i in range(4)))
        self.assertEqual(list(splitter), [
            dict(id='item-01', pipeline=1), # p1 is ahead
            dict(id='item-00'),             # p2 advanced, p1 is skipped
            dict(id='item-01'),             # p2 advanced, p1 no longer ahead
            dict(id='item-03', pipeline=1), # p1 is ahead again
            dict(id='item-02'),             # p2 advanced, p1 is skipped
            dict(id='item-03')              # p2 advanced, p1 no longer ahead
        ])                                  # p1 is done, p2 is done

# Doctest support

class SampleSource(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.encoding = options.get('encoding')
        self.previous = previous
        self.sample = (
            dict(
                id='foo',
                title=u'The Foo Fighters \u2117',
                status=u'\u2117'),
            dict(
                id='bar',
                title=u'Brand Chocolate Bar \u2122',
                status=u'\u2122'),
            dict(id='monty-python',
                 title=u"Monty Python's Flying Circus \u00A9",
                 status=u'\u00A9'),
        )

    def __iter__(self):
        for item in self.previous:
            yield item

        for item in self.sample:
            item = item.copy()
            if self.encoding:
                item['title'] = item['title'].encode(self.encoding)
                item['status'] = item['status'].encode(self.encoding)
            yield item


class RangeSource(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.size = int(options.get('size', 5))

    def __iter__(self):
        for item in self.previous:
            yield item

        for i in range(self.size):
            yield dict(id='item-%02d' % i)


def sectionsSetUp(test):
    setUp(test)

    from collective.transmogrifier.transmogrifier import Transmogrifier
    test.globs['transmogrifier'] = Transmogrifier(test.globs['plone'])

    import collective.transmogrifier.sections
    zcml.load_config('testing.zcml', collective.transmogrifier.sections)

    provideUtility(SampleSource,
        name=u'collective.transmogrifier.sections.tests.samplesource')
    provideUtility(RangeSource,
        name=u'collective.transmogrifier.sections.tests.rangesource')

    import logging
    from zope.testing import loggingsupport
    test.globs['handler'] = loggingsupport.InstalledHandler(
        'logger', level=logging.INFO)


class MockObjectManager(object):

    _last_path = ['']

    def __init__(self, id_='', container=None):
        self.id = id_
        if container is None:
            self._path = ''
        else:
            self._path = posixpath.join(container._path, id_)
        self._last_path[:] = [self._path]

    def _getOb(self, id_, default=_marker):
        if not self.hasObject(id_):
            if default is _marker:
                raise AttributeError(id_)
            else:
                return default
        else:
            return self.__class__(id_, container=self)


def constructorSetUp(test):
    sectionsSetUp(test)

    class MockPortal(MockObjectManager):
        existing = True  # Existing object

        @property
        def portal_types(self):
            return self

        def getTypeInfo(self, type_name):
            self._last_path[:] = ['']
            self._last_type = type_name
            if type_name in ('FooType', 'BarType'):
                return self

        def hasObject(self, id_):
            if isinstance(id_, unicode):
                return False
            if (self._path + '/' + id_).startswith('not/existing'):
                return False
            return True

        constructed = []

        def _constructInstance(self, context, id_):
            if id_ == 'changeme':
                id_ = 'changedByFactory'
            self.constructed.append((self._last_path[0], id_, self._last_type))
            return MockPortal(id_, container=self)

        def _finishConstruction(self, obj):
            return obj

        def getId(self):
            return self.id

    test.globs['plone'] = MockPortal()
    test.globs['transmogrifier'].context = test.globs['plone']

    class ContentSource(SampleSource):
        classProvides(ISectionBlueprint)
        implements(ISection)

        def __init__(self, *args, **kw):
            super(ContentSource, self).__init__(*args, **kw)
            self.sample = (
                dict(_type='FooType', _path='/eggs/foo'),
                dict(_type='FooType', _path='/spam/eggs/foo'),
                dict(_type='FooType', _path='/foo'),
                dict(_type='FooType', _path=u'/unicode/encoded/to/ascii'),
                dict(_type='BarType', _path='not/existing/bar',
                     title='Should not be constructed, not an existing path'),
                dict(_type='FooType', _path='/spam/eggs/existing',
                     title='Should not be constructed, an existing object'),
                dict(_path='/spam/eggs/incomplete',
                     title='Should not be constructed, no type'),
                dict(_type='NonExisting', _path='/spam/eggs/nosuchtype',
                     title='Should not be constructed, not an existing type'),
                dict(_type='FooType', _path='/spam/eggs/changeme',
                     title='Factories are allowed to change the id'),
            )
    provideUtility(ContentSource,
        name=u'collective.transmogrifier.sections.tests.contentsource')


def foldersSetUp(test):
    sectionsSetUp(test)

    class MockPortal(MockObjectManager):

        exists = set()

        def __init__(self, id_='', container=None):
            if container is None:
                self._path = ''
            else:
                self._path = container._path + '/' + id_

        def hasObject(self, id_):
            path = self._path + '/' + id_
            if path in self.exists:
                return True
            self.exists.add(path)
            if isinstance(id_, unicode):
                return False
            if not path.startswith('/existing'):
                return False
            return True

    test.globs['plone'] = MockPortal()
    test.globs['transmogrifier'].context = test.globs['plone']

    class FoldersSource(SampleSource):
        classProvides(ISectionBlueprint)
        implements(ISection)

        def __init__(self, *args, **kw):
            super(FoldersSource, self).__init__(*args, **kw)
            self.sample = (
                dict(_type='Document', _path='/foo'),                   # in root, do nothing
                dict(_type='Document', _path='/existing/foo'),          # in existing folder, do nothing
                dict(_type='Document', _path='/nonexisting/alpha/foo'), # neither parent exists, yield both
                dict(_type='Document', _path='/nonexisting/beta/foo'),  # this time yield only beta
                dict(_type='Document'),                                 # no path key
                dict(_type='Document', _folders_path='/delta/foo'),     # specific path key
            )
    provideUtility(FoldersSource,
        name=u'collective.transmogrifier.sections.tests.folderssource')


def pdbSetUp(test):
    sectionsSetUp(test)

    import pdb
    from collective.transmogrifier.sections import breakpoint

    class Input:
        """A helper to push data onto stdin"""

        def __init__(self, src):
            self.lines = src.split('\n')

        def readline(self):
            line = self.lines.pop(0)
            print line
            return line + '\n'

    def make_stdin(data):
        oldstdin = sys.stdin
        sys.stdin = Input(data)
        breakpoint.BreakpointSection.pdb = pdb.Pdb()

    def reset_stdin(old):
        sys.stdin = old

    test.globs['make_stdin'] = make_stdin
    test.globs['reset_stdin'] = reset_stdin


class HTTPHandler(urllib2.HTTPHandler):

    def http_open(self, req):
        url = req.get_full_url()
        resp = urllib2.addinfourl(
            io.StringIO(), mimetools.Message(io.StringIO()), url)
        if 'redirect' in url:
            resp.code = 301
            resp.msg = 'Permanent'
            resp.info()['Location'] = url.replace('redirect', 'location')
        elif 'location' in url:
            resp.code = 200
            resp.msg = 'Ok'
        else:
            resp.code = 404
            resp.msg = 'Not Found'
        return resp


def urlopenTearDown(test):
    shutil.rmtree('var/tests.urlopener.cache.d')
    tearDown(test)


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(SplitterConditionSectionTests),
        unittest.makeSuite(SplitterSectionTests),
        doctest.DocFileSuite(
            '../../../../docs/source/sections/codec.rst',
            '../../../../docs/source/sections/inserter.rst',
            '../../../../docs/source/sections/manipulator.rst',
            '../../../../docs/source/sections/condition.rst',
            '../../../../docs/source/sections/splitter.rst',
            '../../../../docs/source/sections/savepoint.rst',
            '../../../../docs/source/sections/logger.rst',
            '../../../../docs/source/sections/listsource.rst',
            '../../../../docs/source/sections/xmlwalker.rst',
            setUp=sectionsSetUp, tearDown=tearDown,
            optionflags=doctest.NORMALIZE_WHITESPACE | doctest.REPORT_NDIFF),
        doctest.DocFileSuite(
            '../../../../docs/source/sections/csvsource.rst',
            '../../../../docs/source/sections/dirwalker.rst',
            setUp=sectionsSetUp, tearDown=tearDown,
            optionflags=doctest.NORMALIZE_WHITESPACE | doctest.REPORT_NDIFF
            | doctest.ELLIPSIS),
        doctest.DocFileSuite(
            '../../../../docs/source/sections/urlopener.rst',
            setUp=sectionsSetUp, tearDown=urlopenTearDown,
            optionflags=doctest.NORMALIZE_WHITESPACE | doctest.REPORT_NDIFF
            | doctest.ELLIPSIS),
        doctest.DocFileSuite(
            '../../../../docs/source/sections/constructor.rst',
            setUp=constructorSetUp, tearDown=tearDown,
            optionflags=doctest.NORMALIZE_WHITESPACE | doctest.REPORT_NDIFF),
        doctest.DocFileSuite(
            '../../../../docs/source/sections/folders.rst',
            setUp=foldersSetUp, tearDown=tearDown,
            optionflags=doctest.NORMALIZE_WHITESPACE | doctest.REPORT_NDIFF),
        doctest.DocFileSuite(
            '../../../../docs/source/sections/breakpoint.rst',
            setUp=pdbSetUp, tearDown=tearDown,
            optionflags=doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS),
    ))
