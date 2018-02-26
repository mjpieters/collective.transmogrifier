# -*- coding: utf-8 -*-
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.utils import Condition
from collective.transmogrifier.utils import Matcher
from collective.transmogrifier.utils import pformat_msg
from zope.interface import classProvides
from zope.interface import implements

import logging


class LoggerSection(object):
    """Logs a value of a key."""

    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous

        self.key = options.get('key')
        self.delete = Matcher(*options.get('delete', '').splitlines())
        self.condition = Condition(options.get('condition', 'python:True'),
                                   transmogrifier, name, options)

        self.logger = logging.getLogger(options.get(
            'name', transmogrifier.configuration_id + '.' + name))
        # First check if the level is a named level:
        level = options.get('level', logging.getLevelName(self.logger.level))
        self.level = getattr(logging, level, None)
        if self.level is None:
            # Assume it's an integer:
            self.level = int(level)
        self.logger.setLevel(self.level)

        if self.key is None:
            import pprint
            self.pformat = pprint.PrettyPrinter().pformat

    def __iter__(self):
        for item in self.previous:
            if self.logger.isEnabledFor(self.level) and self.condition(item):
                if self.key is None:
                    copy = {}
                    for key in item.keys():
                        if not self.delete(key)[1]:
                            copy[key] = item[key]
                    msg = pformat_msg(copy)
                else:
                    msg = item.get(self.key, '-- Missing key --')
                self.logger.log(self.level, msg)
            yield item
