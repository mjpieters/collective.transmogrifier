# -*- coding: utf-8 -*-
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.utils import Matcher
from collective.transmogrifier.utils import traverse
from zope.interface import implementer
from zope.interface import provider


def boolean(val):
    return val.lower() in ("yes", "true", "on", "1")


def assequence(val):
    """If a string, make it a sequence

    Returns issingle (True, False), sequence

    """
    if isinstance(val, str):
        return True, (val,)
    return False, val


@provider(ISectionBlueprint)
@implementer(ISection)
class PathResolverSection(object):
    def __init__(self, transmogrifier, name, options, previous):
        self.keys = Matcher(*options["keys"].splitlines())
        self.defer = boolean(options.get("defer-until-present", "no"))
        self.previous = previous
        self._deferred = []
        self.context = transmogrifier.context

    def process_item(self, item, defer=None):
        """Replace paths with objects

        Manipulates item in-place, returns success (True or False). Success
        is defined as 'all paths resolved' if defer is true, and otherwise
        means 'all existing paths resolved'.

        If defer is None, self.defer is used instead.

        """
        if defer is None:
            defer = self.defer
        context = self.context
        resolved = {}

        for key in list(item.keys()):
            match = self.keys(key)[1]
            if match:
                single, paths = assequence(item[key])
                result = [traverse(context, p.lstrip("/"), None) for p in paths]
                if defer and None in result:
                    return False
                if single:
                    result = result[0]
                else:
                    # Strip unresolved items
                    result = [x for x in result if x is not None]
                resolved[key] = result

        item.update(resolved)
        return True

    def process_deferred(self):
        """Process deferred items

        Yields items that can now be completed

        """
        deferred = self._deferred
        self._deferred = []
        for item in deferred:
            if self.process_item(item):
                yield item
            else:
                self._deferred.append(item)

    def __iter__(self):
        for item in self.previous:
            if self.process_item(item):
                yield item
                for item in self.process_deferred():
                    yield item
            else:
                self._deferred.append(item)

        # anything in the queue still needs to be processed
        # without deferring (skipping non-existing items)
        for item in self._deferred:
            self.process_item(item, defer=False)
            yield item
