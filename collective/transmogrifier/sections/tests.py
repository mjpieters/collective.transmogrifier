import itertools
import pprint
import unittest
from zope.component import provideUtility
from zope.interface import classProvides, implements
from zope.testing import doctest
from collective.transmogrifier.interfaces import ISectionBlueprint, ISection
from collective.transmogrifier.tests import setUp, tearDown
from Products.Five import zcml

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

class PrettyPrinter(object):
    classProvides(ISectionBlueprint)
    implements(ISection)
    
    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.pprint = pprint.PrettyPrinter().pprint
    
    def __iter__(self):
        for item in self.previous:
            self.pprint(item)
            yield item

def sectionsSetUp(test):
    setUp(test)
        
    from collective.transmogrifier.transmogrifier import Transmogrifier
    test.globs['transmogrifier'] = Transmogrifier(test.globs['plone'])
    
    import zope.component
    import collective.transmogrifier.sections
    zcml.load_config('meta.zcml', zope.component)
    zcml.load_config('configure.zcml', collective.transmogrifier.sections)
    
    provideUtility(SampleSource,
        name=u'collective.transmogrifier.sections.tests.samplesource')
    provideUtility(RangeSource,
        name=u'collective.transmogrifier.sections.tests.rangesource')
    provideUtility(PrettyPrinter,
        name=u'collective.transmogrifier.sections.tests.pprinter')

def portalTransformsSetUp(test):
    sectionsSetUp(test)
    
    class MockPortalTransforms(object):
        def __call__(self, transform, data):
            return 'Transformed %r using the %s transform' % (data, transform)
        def convertToData(self, target, data, mimetype=None):
            if mimetype is not None:
                return 'Transformed %r from %s to %s' % (
                    data, mimetype, target)
            else:
                return 'Transformed %r to %s' % (data, target)
    test.globs['plone'].portal_transforms = MockPortalTransforms()

def constructorSetUp(test):
    sectionsSetUp(test)
    
    class MockPortal(object):
        existing = True # Existing object
        
        @property
        def portal_types(self): return self
        def getTypeInfo(self, type_name):
            if type_name in ('FooType', 'BarType'): return True
        
        _last_path = None
        def unrestrictedTraverse(self, path, default):
            if path[0] == '/':
                return default # path is absolute
            if path == 'not/existing':
                return default
            self._last_path = path
            return self
        
        constructed = ()
        def invokeFactory(self, id, type_name):
            if id == 'changeme':
                id = 'changedByFactory'
            self.constructed += ((self._last_path, id, type_name),)
            return id
    
    test.globs['plone'] = MockPortal()
    test.globs['transmogrifier'].portal = test.globs['plone']
    
    class ContentSource(SampleSource):
        classProvides(ISectionBlueprint)
        implements(ISection)
        
        def __init__(self, *args, **kw):
            super(ContentSource, self).__init__(*args, **kw)
            self.sample = (
                dict(_type='FooType', _path='/spam/eggs/foo'),
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

def aTSchemaUpdaterSetUp(test):
    sectionsSetUp(test)
    
    class MockField(object):
        def __init__(self, name):
            self.name = name
        def getName(self):
            return self.name
        _instance = None
        def getMutator(self, obj):
            self._instance = obj
            return self
        def __call__(self, val):
            self._instance._fieldSet(self.name, val)
    
    from Products.Archetypes.interfaces import IBaseObject
    class MockPortal(object):
        implements(IBaseObject)
        
        _last_path = None
        def unrestrictedTraverse(self, path, default):
            if path[0] == '/':
                return default # path is absolute
            if path == 'not/existing/bar':
                return default
            if path.endswith('/notatcontent'):
                return object()
            self._last_path = path
            return self
        
        def Schema(self):
            return self
        def editableFields(self):
            return (MockField('fieldone'), MockField('fieldtwo'),
                    MockField('title'))
        
        updated = ()
        def _fieldSet(self, name, val):
            self.updated += ((self._last_path, name, val),)
    
    test.globs['plone'] = MockPortal()
    test.globs['transmogrifier'].portal = test.globs['plone']
    
    class SchemaSource(SampleSource):
        classProvides(ISectionBlueprint)
        implements(ISection)
        
        def __init__(self, *args, **kw):
            super(SchemaSource, self).__init__(*args, **kw)
            self.sample = (
                dict(_path='/spam/eggs/foo', fieldone='one value', 
                     fieldtwo=2, nosuchfield='ignored'),
                dict(_path='not/existing/bar', fieldone='one value',
                     title='Should not be updated, not an existing path'),
                dict(fieldone='one value',
                     title='Should not be updated, no path'),
                dict(_path='/spam/eggs/notatcontent', fieldtwo=2,
                     title='Should not be updated, not an AT base object'),
            )
    provideUtility(SchemaSource,
        name=u'collective.transmogrifier.sections.tests.schemasource')

def workflowUpdaterSetUp(test):
    sectionsSetUp(test)
    
    from Products.CMFCore.WorkflowCore import WorkflowException
    
    class MockPortal(object):
        _last_path = None
        def unrestrictedTraverse(self, path, default):
            if path[0] == '/':
                return default # path is absolute
            if path == 'not/existing/bar':
                return default
            self._last_path = path
            return self
        
        @property
        def portal_workflow(self):
            return self
        
        updated = ()
        def doActionFor(self, ob, action):
            assert ob == self
            if action == 'nonsuch':
                raise WorkflowException('Test exception')
            self.updated += ((self._last_path, action),)

    test.globs['plone'] = MockPortal()
    test.globs['transmogrifier'].portal = test.globs['plone']

    class WorkflowSource(SampleSource):
        classProvides(ISectionBlueprint)
        implements(ISection)

        def __init__(self, *args, **kw):
            super(WorkflowSource, self).__init__(*args, **kw)
            self.sample = (
                dict(_path='/spam/eggs/foo', _transitions='spam'),
                dict(_path='/spam/eggs/baz', _transitions=('spam', 'eggs')),
                dict(_path='not/existing/bar', _transitions=('spam', 'eggs'),
                     title='Should not be updated, not an existing path'),
                dict(_path='spam/eggs/incomplete',
                     title='Should not be updated, no transitions'),
                dict(_path='/spam/eggs/nosuchtransition', 
                     _transitions=('nonsuch',),
                     title='Should not be updated, no such transition'),
            )
    provideUtility(WorkflowSource,
        name=u'collective.transmogrifier.sections.tests.workflowsource')


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(SplitterConditionSectionTests),
        unittest.makeSuite(SplitterSectionTests),
        doctest.DocFileSuite(
            'codec.txt', 'inserter.txt', 'manipulator.txt', 'condition.txt',
            'splitter.txt', 'savepoint.txt', 'csvsource.txt',
            setUp=sectionsSetUp, tearDown=tearDown),
        doctest.DocFileSuite(
            'portaltransforms.txt',
            setUp=portalTransformsSetUp, tearDown=tearDown),
        doctest.DocFileSuite(
            'constructor.txt',
            setUp=constructorSetUp, tearDown=tearDown),
        doctest.DocFileSuite(
            'atschemaupdater.txt',
            setUp=aTSchemaUpdaterSetUp, tearDown=tearDown),
        doctest.DocFileSuite(
            'workflowupdater.txt',
            setUp=workflowUpdaterSetUp, tearDown=tearDown),
    ))
