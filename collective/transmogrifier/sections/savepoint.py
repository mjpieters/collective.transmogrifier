import transaction
from zope.interface import classProvides, implements
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.interfaces import ISection

class SavepointSection(object):
    classProvides(ISectionBlueprint)
    implements(ISection)
    
    def __init__(self, transmogrifier, name, options, previous):
        self.every = int(options.get('every', 1000))
        self.previous = previous
    
    def __iter__(self):
        count = 0
        for item in self.previous:
            count = (count + 1) % self.every
            if count == 0:
                transaction.savepoint(optimistic=True)
            yield item
