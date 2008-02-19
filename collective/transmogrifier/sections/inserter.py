from zope.interface import classProvides, implements
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.utils import Expression

class InserterSection(object):
    classProvides(ISectionBlueprint)
    implements(ISection)
    
    def __init__(self, transmogrifier, name, options, previous):
        self.key = Expression(options['key'], transmogrifier, name, options)
        self.value = Expression(options['value'], transmogrifier, name,
                                options)
        self.previous = previous
    
    def __iter__(self):
        for item in self.previous:
            item[self.key(item)] = self.value(item)
            yield item
