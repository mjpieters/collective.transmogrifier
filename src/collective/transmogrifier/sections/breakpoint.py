import logging

from zope.interface import classProvides, implements

from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.utils import Condition
from pdb import set_trace

# Breaks on a condition.

class BreakpointSection(object):
    classProvides(ISectionBlueprint)
    implements(ISection)
    
    def __init__(self, transmogrifier, name, options, previous):
        condition = options['condition']
        self.condition = Condition(condition, transmogrifier, name, options)
        self.previous = previous
        
    def __iter__(self):
        for item in self.previous:
            if self.condition(item):
                set_trace() # Break!
            yield item
