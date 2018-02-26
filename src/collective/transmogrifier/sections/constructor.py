# -*- coding: utf-8 -*-
from Acquisition import aq_base
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.utils import defaultMatcher
from collective.transmogrifier.utils import traverse
from Products.CMFCore.utils import getToolByName
from zope.interface import classProvides
from zope.interface import implements

import logging
import posixpath


logger = logging.getLogger('collective.transmogrifier.constructor')


class ConstructorSection(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.context = transmogrifier.context
        self.ttool = getToolByName(self.context, 'portal_types')

        self.typekey = defaultMatcher(options, 'type-key', name, 'type',
                                      ('portal_type', 'Type'))
        self.pathkey = defaultMatcher(options, 'path-key', name, 'path')
        self.required = bool(options.get('required'))

    def __iter__(self):
        for item in self.previous:
            keys = item.keys()
            typekey = self.typekey(*keys)[0]
            pathkey = self.pathkey(*keys)[0]

            if not (typekey and pathkey):
                logger.warn('Not enough info for item: %s' % item)
                yield item; continue

            type_, path = item[typekey], item[pathkey]

            fti = self.ttool.getTypeInfo(type_)
            if fti is None:
                logger.warn('Not an existing type: %s' % type_)
                yield item; continue

            path = path.encode('ASCII')
            container, id = posixpath.split(path.strip('/'))
            context = traverse(self.context, container, None)
            if context is None:
                error = 'Container %s does not exist for item %s' % (
                    container, path)
                if self.required:
                    raise KeyError(error)
                logger.warn(error)
                yield item
                continue

            if getattr(aq_base(context), id, None) is not None:  # item exists
                yield item; continue

            try:
                obj = fti._constructInstance(context, id)
            except ValueError:
                error = 'Could not create type %s with id %s at %s' % (
                    type_, id, path)
                logger.warn(error)
                yield item
                continue

            # For CMF <= 2.1 (aka Plone 3)
            if hasattr(fti, '_finishConstruction'):
                obj = fti._finishConstruction(obj)

            if obj.getId() != id:
                item[pathkey] = posixpath.join(container, obj.getId())

            yield item
