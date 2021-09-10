# -*- coding: utf-8 -*-
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.utils import Condition
from collective.transmogrifier.utils import Expression
from zope.interface import implementer
from zope.interface import provider


@provider(ISectionBlueprint)
@implementer(ISection)
class InserterSection(object):
    def __init__(self, transmogrifier, name, options, previous):
        self.key = Expression(options["key"], transmogrifier, name, options)
        self.value = Expression(options["value"], transmogrifier, name, options)
        self.condition = Condition(
            options.get("condition", "python:True"), transmogrifier, name, options
        )
        self.previous = previous

    def __iter__(self):
        for item in self.previous:
            key = self.key(item)
            if self.condition(item, key=key):
                item[key] = self.value(item, key=key)
            yield item
