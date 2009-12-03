import copy
from zope.interface import classProvides, implements
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.utils import Matcher, Expression, Condition

class ManipulatorSection(object):
    classProvides(ISectionBlueprint)
    implements(ISection)
    
    def __init__(self, transmogrifier, name, options, previous):
        keys = options.get('keys') or ''
        self.keys = Matcher(*keys.splitlines())
        if keys:
            self.dest = Expression(options['destination'], transmogrifier,
                                   name, options)
        self.delete = Matcher(*options.get('delete', '').splitlines())
        self.condition = Condition(options.get('condition', 'python:True'),
                                   transmogrifier, name, options)
        self.previous = previous
    
    def __iter__(self):
        for item in self.previous:
            if self.condition(item):
                for key in item.keys():
                    match = self.keys(key)[1]
                    if match:
                        dest = self.dest(item, key=key, match=match)
                        item[dest] = copy.deepcopy(item[key])
                    if self.delete(key)[1]:
                        del item[key]
            yield item
