# -*- coding: utf-8 -*-
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.utils import Condition
from pdb import Pdb
from zope.interface import provider
from zope.interface import implementer

import sys


# Breaks on a condition.


@provider(ISectionBlueprint)
@implementer(ISection)
class BreakpointSection(object):

    pdb = Pdb()

    def __init__(self, transmogrifier, name, options, previous):
        condition = options["condition"]
        self.condition = Condition(condition, transmogrifier, name, options)
        self.previous = previous

    def __iter__(self):
        for item in self.previous:
            if self.condition(item):
                self.pdb.set_trace(sys._getframe().f_back)  # Break!
            yield item
