from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.sections.urlopener import get_message
from collective.transmogrifier.tests import setUp
from collective.transmogrifier.tests import tearDown
from Zope2.App import zcml
from zope.component import provideUtility
from zope.interface import implementer
from zope.interface import provider

import doctest
import io
import itertools
import posixpath
import re
import shutil
import six
import sys
import unittest


_marker = object()


def get_next_method(iterator):
    """
    Returns the method used by the built-in next function, depending on the
    Python version.
    """
    # BBB: Python 2 uses method next in iterators. Python 3 uses __next__
    if six.PY2:
        return iterator.next
    return iterator.__next__


class SplitterConditionSectionTests(unittest.TestCase):
    def _makeOne(self, previous, condition=None):
        from .splitter import SplitterConditionSection

        return SplitterConditionSection(condition, previous)

    def testIterates(self):
        section = self._makeOne(iter(list(range(10))))
        self.assertEqual(list(range(10)), list(section))

    def testCondition(self):
        section = self._makeOne(iter(list(range(10))), lambda x: x % 2)
        self.assertEqual(list(range(1, 10, 2)), list(section))

    def testAhead(self):
        section = self._makeOne(iter(list(range(3))))

        self.assertEqual(section.ahead, 0)
        self.assertFalse(section.isAhead)

        next(section)
        self.assertEqual(section.ahead, 1)
        self.assertTrue(section.isAhead)
        self.assertEqual(section.ahead, 0)
        self.assertFalse(section.isAhead)

        next(section)
        next(section)
        self.assertEqual(section.ahead, 2)
        self.assertTrue(section.isAhead)
        self.assertEqual(section.ahead, 1)
        self.assertTrue(section.isAhead)
        self.assertEqual(section.ahead, 0)
        self.assertFalse(section.isAhead)

        self.assertRaises(StopIteration, get_next_method(section))
        self.assertEqual(section.ahead, 1)
        self.assertTrue(section.isAhead)
        self.assertEqual(section.ahead, 0)
        self.assertFalse(section.isAhead)

    def testWillMatch(self):
        section = self._makeOne(iter(list(range(2))), lambda x: x % 2)

        self.assertFalse(section.willMatch)
        self.assertTrue(section.willMatch)
        self.assertEqual(next(section), 1)
        self.assertFalse(section.willMatch)
        self.assertRaises(StopIteration, get_next_method(section))

        section = self._makeOne(iter(list(range(3))), lambda x: x < 1)
        self.assertTrue(section.willMatch)
        self.assertTrue(section.willMatch)
        self.assertEqual(next(section), 0)
        self.assertFalse(section.willMatch)
        self.assertRaises(StopIteration, get_next_method(section))

    def testIsDone(self):
        section = self._makeOne(iter(list(range(1))))

        self.assertFalse(section.isDone)
        next(section)
        self.assertTrue(section.isDone)
        self.assertRaises(StopIteration, get_next_method(section))

    def testCopy(self):
        orig, source = itertools.tee((dict(foo=i) for i in range(2)), 2)
        section = self._makeOne(source)
        for original, yielded in zip(orig, section):
            self.assertEqual(original, yielded)
            self.assertFalse(original is yielded)


class SplitterSectionTests(unittest.TestCase):
    def _makeOne(self, transmogrifier, options, previous):
        from .splitter import SplitterSection

        return SplitterSection(transmogrifier, "unittest", options, previous)

    def testAtLeastTwo(self):
        self.assertRaises(ValueError, self._makeOne, {}, {}, iter(()))
        self.assertRaises(ValueError, self._makeOne, {}, {"pipeline-1": ""}, iter(()))
        # Shouldn't raise
        self._makeOne({}, {"pipeline-1": "", "pipeline-2": ""}, iter(()))

    def testInsertExtra(self):
        @implementer(ISection)
        class Inserter:
            def __init__(self, transmogrifier, name, options, previous):
                self.previous = previous

            def __iter__(self):
                count = 0
                for item in self.previous:
                    item["pipeline"] = 1
                    yield item
                    yield dict(id="extra-%02d" % count)
                    count += 1

        provideUtility(
            Inserter, ISectionBlueprint, name="collective.transmogrifier.tests.inserter"
        )
        splitter = self._makeOne(
            dict(inserter=dict(blueprint="collective.transmogrifier.tests.inserter")),
            {"pipeline-1": "inserter", "pipeline-2": ""},
            (dict(id="item-%02d" % i) for i in range(3)),
        )
        self.assertEqual(
            list(splitter),
            [
                dict(id="item-00", pipeline=1),  # p1 advanced, look at p2
                dict(id="item-00"),  # p2 advanced, look at p1
                dict(id="extra-00"),  # p1 did not advance
                dict(id="item-01", pipeline=1),  # p1 advanced, look at p2
                dict(id="item-01"),  # p2 advanced, look at p1
                dict(id="extra-01"),  # p1 did not advance
                dict(id="item-02", pipeline=1),  # p1 advanced, condition isDone
                dict(id="extra-02"),  # last in p1 after isDone, l.a. p2
                dict(id="item-02"),  # p2 advanced
            ],
        )  # p2 is done

    def testSkipItems(self):
        @implementer(ISection)
        class Skip:
            def __init__(self, transmogrifier, name, options, previous):
                self.previous = previous

            def __iter__(self):
                count = 0
                for item in self.previous:
                    if count % 2:
                        item["pipeline"] = 1
                        yield item
                    count += 1

        provideUtility(
            Skip, ISectionBlueprint, name="collective.transmogrifier.tests.skip"
        )
        splitter = self._makeOne(
            dict(skip=dict(blueprint="collective.transmogrifier.tests.skip")),
            {"pipeline-1": "skip", "pipeline-2": ""},
            (dict(id="item-%02d" % i) for i in range(4)),
        )
        self.assertEqual(
            list(splitter),
            [
                dict(id="item-01", pipeline=1),  # p1 is ahead
                dict(id="item-00"),  # p2 advanced, p1 is skipped
                dict(id="item-01"),  # p2 advanced, p1 no longer ahead
                dict(id="item-03", pipeline=1),  # p1 is ahead again
                dict(id="item-02"),  # p2 advanced, p1 is skipped
                dict(id="item-03"),  # p2 advanced, p1 no longer ahead
            ],
        )  # p1 is done, p2 is done


# Doctest support


@provider(ISectionBlueprint)
@implementer(ISection)
class SampleSource:
    def __init__(self, transmogrifier, name, options, previous):
        self.encoding = options.get("encoding")
        self.previous = previous
        self.sample = (
            dict(id="foo", title="The Foo Fighters \u2117", status="\u2117"),
            dict(id="bar", title="Brand Chocolate Bar \u2122", status="\u2122"),
            dict(
                id="monty-python",
                title="Monty Python's Flying Circus \u00A9",
                status="\u00A9",
            ),
        )

    def __iter__(self):
        for item in self.previous:
            yield item

        for item in self.sample:
            item = item.copy()
            if self.encoding:
                item["title"] = item["title"].encode(self.encoding)
                item["status"] = item["status"].encode(self.encoding)
            yield item


@provider(ISectionBlueprint)
@implementer(ISection)
class RangeSource:
    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.size = int(options.get("size", 5))

    def __iter__(self):
        yield from self.previous

        for i in range(self.size):
            yield dict(id="item-%02d" % i)


def sectionsSetUp(test):
    setUp(test)

    from collective.transmogrifier.transmogrifier import Transmogrifier

    test.globs["transmogrifier"] = Transmogrifier(test.globs["plone"])

    import collective.transmogrifier.sections

    zcml.load_config("testing.zcml", collective.transmogrifier.sections)

    provideUtility(
        SampleSource, name="collective.transmogrifier.sections.tests.samplesource"
    )
    provideUtility(
        RangeSource, name="collective.transmogrifier.sections.tests.rangesource"
    )

    from zope.testing import loggingsupport

    import logging

    test.globs["handler"] = loggingsupport.InstalledHandler(
        "logger", level=logging.INFO
    )


class MockObjectManager:

    _last_path = [""]

    def __init__(self, id_="", container=None):
        self.id = id_
        if container is None:
            self._path = ""
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
            self._last_path[:] = [""]
            self._last_type = type_name
            if type_name in ("FooType", "BarType"):
                return self

        def hasObject(self, id_):
            if six.PY2 and isinstance(id_, unicode):
                return False
            if (self._path + "/" + id_).startswith("not/existing"):
                return False
            return True

        constructed = []

        def _constructInstance(self, context, id_):
            if id_ == "changeme":
                id_ = "changedByFactory"
            self.constructed.append((self._last_path[0], id_, self._last_type))
            return MockPortal(id_, container=self)

        def _finishConstruction(self, obj):
            return obj

        def getId(self):
            return self.id

    test.globs["plone"] = MockPortal()
    test.globs["transmogrifier"].context = test.globs["plone"]

    @provider(ISectionBlueprint)
    @implementer(ISection)
    class ContentSource(SampleSource):
        def __init__(self, *args, **kw):
            super().__init__(*args, **kw)
            self.sample = (
                dict(_type="FooType", _path="/eggs/foo"),
                dict(_type="FooType", _path="/spam/eggs/foo"),
                dict(_type="FooType", _path="/foo"),
                dict(_type="FooType", _path="/unicode/encoded/to/ascii"),
                dict(
                    _type="BarType",
                    _path="not/existing/bar",
                    title="Should not be constructed, not an existing path",
                ),
                dict(
                    _type="FooType",
                    _path="/spam/eggs/existing",
                    title="Should not be constructed, an existing object",
                ),
                dict(
                    _path="/spam/eggs/incomplete",
                    title="Should not be constructed, no type",
                ),
                dict(
                    _type="NonExisting",
                    _path="/spam/eggs/nosuchtype",
                    title="Should not be constructed, not an existing type",
                ),
                dict(
                    _type="FooType",
                    _path="/spam/eggs/changeme",
                    title="Factories are allowed to change the id",
                ),
            )

    provideUtility(
        ContentSource, name="collective.transmogrifier.sections.tests.contentsource"
    )


def foldersSetUp(test):
    sectionsSetUp(test)

    class MockPortal(MockObjectManager):

        exists = set()

        def __init__(self, id_="", container=None):
            if container is None:
                self._path = ""
            else:
                self._path = container._path + "/" + id_

        def hasObject(self, id_):
            path = self._path + "/" + id_
            if path in self.exists:
                return True
            self.exists.add(path)
            if six.PY2 and isinstance(id_, unicode):
                return False
            if not path.startswith("/existing"):
                return False
            return True

    test.globs["plone"] = MockPortal()
    test.globs["transmogrifier"].context = test.globs["plone"]

    @provider(ISectionBlueprint)
    @implementer(ISection)
    class FoldersSource(SampleSource):
        def __init__(self, *args, **kw):
            super().__init__(*args, **kw)
            self.sample = (
                dict(_type="Document", _path="/foo"),
                # in root, do nothing
                dict(_type="Document", _path="/existing/foo"),
                # in existing folder, do nothing
                dict(_type="Document", _path="/nonexisting/alpha/foo"),
                # neither parent exists, yield both
                dict(_type="Document", _path="/nonexisting/beta/foo"),
                # this time yield only beta
                # no path key
                dict(_type="Document"),
                dict(_type="Document", _folders_path="/delta/foo"),
                # specific path key
            )

    provideUtility(
        FoldersSource, name="collective.transmogrifier.sections.tests.folderssource"
    )


def pdbSetUp(test):
    sectionsSetUp(test)

    from collective.transmogrifier.sections import breakpoint

    import pdb

    class Input:

        """A helper to push data onto stdin"""

        def __init__(self, src):
            self.lines = src.split("\n")

        def readline(self):
            line = self.lines.pop(0)
            print(line)
            return line + "\n"

    def make_stdin(data):
        sys.stdin = Input(data)
        breakpoint.BreakpointSection.pdb = pdb.Pdb()

    def reset_stdin(old):
        sys.stdin = old

    test.globs["make_stdin"] = make_stdin
    test.globs["reset_stdin"] = reset_stdin


class HTTPHandler(six.moves.urllib.request.HTTPHandler):
    def http_open(self, req):
        url = req.get_full_url()
        resp = six.moves.urllib.response.addinfourl(
            io.StringIO(),
            get_message(),
            url,
        )
        if "redirect" in url:
            resp.code = 301
            resp.msg = "Permanent"
            resp.info()["Location"] = url.replace("redirect", "location")
        elif "location" in url:
            resp.code = 200
            resp.msg = "Ok"
        else:
            resp.code = 404
            resp.msg = "Not Found"
        return resp


def urlopenTearDown(test):
    shutil.rmtree("var/tests.urlopener.cache.d")
    tearDown(test)


class Py23DocChecker(doctest.OutputChecker):
    def __init__(self):
        """Constructor"""

    def transformer_py2_output(self, got):
        """Handles differences in output between Python 2 and Python 3."""
        if six.PY2:
            got = re.sub("u'", "'", got)
            got = re.sub('u"', '"', got)

            got = re.sub("\\'\\\\u2117\\'", "'\xe2\x84\x97'", got)
            got = re.sub("\\\\u2122", "\xe2\x84\xa2", got)
            got = re.sub("\\'\\\\xa9\\'", "'\xc2\xa9'", got)

            # Adaptation to manipulator.rst test in Python 2
            got = re.sub("\\\\u2117", "\xe2\x84\x97", got)
            got = re.sub("\\\\\\xe2\\x84\\x97", "\\\\\\u2117", got)
            got = re.sub("\\\\xa9", "\xc2\xa9", got)
            got = re.sub("\\\\\\xc2\xa9", "\\\\\\xa9", got)

        return got

    def check_output(self, want, got, optionflags):
        got = self.transformer_py2_output(got)
        return doctest.OutputChecker.check_output(self, want, got, optionflags)

    def output_difference(self, example, got, optionflags):
        got = self.transformer_py2_output(got)
        return doctest.OutputChecker.output_difference(self, example, got, optionflags)


def test_suite():
    return unittest.TestSuite(
        (
            unittest.defaultTestLoader.loadTestsFromTestCase(SplitterConditionSectionTests),
            unittest.defaultTestLoader.loadTestsFromTestCase(SplitterSectionTests),
            doctest.DocFileSuite(
                "../../../../docs/source/sections/codec.rst",
                "../../../../docs/source/sections/inserter.rst",
                "../../../../docs/source/sections/manipulator.rst",
                "../../../../docs/source/sections/condition.rst",
                "../../../../docs/source/sections/splitter.rst",
                "../../../../docs/source/sections/savepoint.rst",
                "../../../../docs/source/sections/logger.rst",
                "../../../../docs/source/sections/listsource.rst",
                "../../../../docs/source/sections/xmlwalker.rst",
                setUp=sectionsSetUp,
                tearDown=tearDown,
                optionflags=doctest.NORMALIZE_WHITESPACE | doctest.REPORT_NDIFF,
                checker=Py23DocChecker(),
            ),
            doctest.DocFileSuite(
                "../../../../docs/source/sections/csvsource.rst",
                "../../../../docs/source/sections/dirwalker.rst",
                setUp=sectionsSetUp,
                tearDown=tearDown,
                optionflags=doctest.NORMALIZE_WHITESPACE
                | doctest.REPORT_NDIFF
                | doctest.ELLIPSIS,
            ),
            doctest.DocFileSuite(
                "../../../../docs/source/sections/urlopener.rst",
                setUp=sectionsSetUp,
                tearDown=urlopenTearDown,
                optionflags=doctest.NORMALIZE_WHITESPACE
                | doctest.REPORT_NDIFF
                | doctest.ELLIPSIS,
            ),
            doctest.DocFileSuite(
                "../../../../docs/source/sections/constructor.rst",
                setUp=constructorSetUp,
                tearDown=tearDown,
                optionflags=doctest.NORMALIZE_WHITESPACE | doctest.REPORT_NDIFF,
                checker=Py23DocChecker(),
            ),
            doctest.DocFileSuite(
                "../../../../docs/source/sections/folders.rst",
                setUp=foldersSetUp,
                tearDown=tearDown,
                optionflags=doctest.NORMALIZE_WHITESPACE | doctest.REPORT_NDIFF,
            ),
            doctest.DocFileSuite(
                "../../../../docs/source/sections/breakpoint.rst",
                setUp=pdbSetUp,
                tearDown=tearDown,
                optionflags=doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS,
            ),
        )
    )
