from zope.interface import classProvides, implements
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.utils import Expression, Condition

class InserterSection(object):
    classProvides(ISectionBlueprint)
    implements(ISection)
    
    def __init__(self, transmogrifier, name, options, previous):
        self.key = Expression(options['key'], transmogrifier, name, options)
        self.value = Expression(options['value'], transmogrifier, name,
                                options)
        self.condition = options.get('condition')
        if self.condition is not None:
            self.condition = Condition(self.condition, transmogrifier, name,
                                       options)
        self.previous = previous
    
    def __iter__(self):
        for item in self.previous:
            if self.condition is None or self.condition(item):
                item[self.key(item)] = self.value(item)
            yield item
