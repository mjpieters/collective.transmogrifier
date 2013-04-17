from zope.interface import classProvides
from zope.interface import implements
from zope.annotation.interfaces import IAnnotations

from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.utils import Condition

LISTKEY = 'collective.transmogrifier.sections.listsource'


class ListSource(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.items = IAnnotations(transmogrifier).setdefault(
            LISTKEY, {}).setdefault(name, [])

    def __iter__(self):
        for item in self.previous:
            yield item

            while self.items:
                yield self.items.pop(0)


class ListAppender(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.condition = Condition(options.get('condition', 'python:True'),
                                   transmogrifier, name, options)
        self.items = IAnnotations(transmogrifier)[LISTKEY][options['section']]

    def __iter__(self):
        for item in self.previous:
            if self.condition(item):
                self.items.append(item)
            else:
                yield item
