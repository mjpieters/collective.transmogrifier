# -*- coding: utf-8 -*-
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.utils import Condition
from collective.transmogrifier.utils import Expression
from zope.annotation.interfaces import IAnnotations
from zope.interface import classProvides
from zope.interface import implements


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
                appended = self.items.pop(0)
                yield appended


class ListAppender(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.condition = Condition(options.get('condition', 'python:True'),
                                   transmogrifier, name, options)
        self.items = IAnnotations(transmogrifier)[LISTKEY][options['section']]

        self.keys = Expression(
            options.get('keys', 'nothing'), transmogrifier, name, options)
        self.copykeys = Expression(
            options.get('copy-keys', 'nothing'), transmogrifier, name, options)

    def __iter__(self):
        for item in self.previous:
            if self.condition(item):
                keys = self.keys(item)
                copykeys = self.copykeys(item)
                if keys or copykeys:
                    new_item = dict(
                        (key, item.pop(key)) for key in keys if key in item)
                    new_item.update(
                        (key, item[key]) for key in copykeys if key in item)
                    if new_item:
                        self.items.append(new_item)
                    yield item
                else:
                    self.items.append(item)
            else:
                yield item
