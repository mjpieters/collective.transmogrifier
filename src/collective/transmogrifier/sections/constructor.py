# -*- coding: utf-8 -*-
from Acquisition import aq_base
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.utils import defaultMatcher
from collective.transmogrifier.utils import traverse
from Products.CMFCore.utils import getToolByName
from zExceptions import BadRequest
from zope.interface import implementer
from zope.interface import provider

import logging
import posixpath
import six


logger = logging.getLogger('collective.transmogrifier.constructor')

@provider(ISectionBlueprint)
@implementer(ISection)
class ConstructorSection(object):

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
            keys = list(item.keys())
            typekey = self.typekey(*keys)[0]
            pathkey = self.pathkey(*keys)[0]

            if not (typekey and pathkey):
                logger.warning('Not enough info for item: %s' % item)
                yield item; continue

            type_, path = item[typekey], item[pathkey]

            fti = self.ttool.getTypeInfo(type_)
            if fti is None:
                logger.warning('Not an existing type: %s' % type_)
                yield item; continue

            if six.PY2:
                path = path.encode('ASCII')
            container, id = posixpath.split(path.strip('/'))
            context = traverse(self.context, container, None)
            if context is None:
                error = 'Container %s does not exist for item %s' % (
                    container, path)
                if self.required:
                    raise KeyError(error)
                logger.warning(error)
                yield item
                continue

            if getattr(aq_base(context), id, None) is not None:  # item exists
                yield item; continue

            try:
                obj = fti._constructInstance(context, id)
            except (BadRequest, ValueError):
                error = 'Could not create type %s with id %s at %s' % (
                    type_, id, path)
                logger.warning(error)
                yield item
                continue

            # For CMF <= 2.1 (aka Plone 3)
            if hasattr(fti, '_finishConstruction'):
                obj = fti._finishConstruction(obj)

            if obj.getId() != id:
                item[pathkey] = posixpath.join(container, obj.getId())

            yield item
