import logging

from zope.interface import classProvides, implements

from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.utils import Condition
try:
    # use ipdb if found
    from ipdb import set_trace
except ImportError:
    from pdb import set_trace

# Breaks on a condition.

class BreakpointSection(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        condition = options.get('condition')
        if condition is not None:
            self.condition = Condition(condition, transmogrifier, name, options)
        else:
            # say we want to break for every item
            # before the next section
            # yes, like placing "condition=python:True"
            # but for lazy people
            self.condition = None
        self.previous = previous

    def __iter__(self):
        for item in self.previous:
            if self.condition is not None:
                if self.condition(item):
                    set_trace() # Break!
            else:
                set_trace()
            yield item
