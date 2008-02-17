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

# Doctest support

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
    test.globs.update(dict(
        transmogrifier=Transmogrifier(test.globs['plone'])))
    
    import zope.component
    import collective.transmogrifier.sections
    zcml.load_config('meta.zcml', zope.component)
    zcml.load_config('configure.zcml', collective.transmogrifier.sections)
    
    provideUtility(RangeSource,
        name=u'collective.transmogrifier.sections.tests.rangesource')
    provideUtility(PrettyPrinter,
        name=u'collective.transmogrifier.sections.tests.pprinter')

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(SplitterConditionSectionTests),
        doctest.DocFileSuite(
            'splitter.txt',
            setUp=sectionsSetUp, tearDown=tearDown),
    ))

    return suite
