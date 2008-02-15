import pprint
import unittest
from zope.component import provideUtility
from zope.interface import classProvides, implements
from zope.testing import doctest
from collective.transmogrifier.interfaces import ISectionBlueprint, ISection
from collective.transmogrifier.tests import setUp, tearDown

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
    
    from splitter import SplitterSection
    provideUtility(SplitterSection,
        name=u'collective.transmogrifier.sections.splitter')
    
    provideUtility(RangeSource,
        name=u'collective.transmogrifier.sections.tests.rangesource')
    provideUtility(PrettyPrinter,
        name=u'collective.transmogrifier.sections.tests.pprinter')

def test_suite():
    return unittest.TestSuite((
        doctest.DocFileSuite(
            'splitter.txt',
            setUp=sectionsSetUp, tearDown=tearDown),
    ))

    return suite
