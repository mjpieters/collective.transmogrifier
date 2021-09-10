# -*- coding: utf-8 -*-
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.interfaces import ISectionBlueprint
from zope.interface import provider
from zope.interface import implementer

import transaction


@provider(ISectionBlueprint)
@implementer(ISection)
class SavepointSection(object):
    def __init__(self, transmogrifier, name, options, previous):
        self.every = int(options.get("every", 1000))
        self.previous = previous

    def __iter__(self):
        count = 0
        for item in self.previous:
            count = (count + 1) % self.every
            if count == 0:
                transaction.savepoint(optimistic=True)
            yield item
