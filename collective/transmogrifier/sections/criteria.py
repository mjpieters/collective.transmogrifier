from zope.interface import classProvides, implements
from zope.component import queryUtility

from collective.transmogrifier.interfaces import ISection, ISectionBlueprint
from collective.transmogrifier.utils import Matcher
from collective.transmogrifier.utils import defaultKeys

from Acquisition import aq_base
from Products.ATContentTypes.interface import IATTopic


class CriterionAdder(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.context = transmogrifier.context

        if 'path-key' in options:
            pathkeys = options['path-key'].splitlines()
        else:
            pathkeys = defaultKeys(options['blueprint'], name, 'path')
        self.pathkey = Matcher(*pathkeys)
        if 'criterion-key' in options:
            criterionkeys = options['criterion-key'].splitlines()
        else:
            criterionkeys = defaultKeys(options['blueprint'], name, 'criterion')
        self.criterionkey = Matcher(*criterionkeys)
        if 'field-key' in options:
            fieldkeys = options['field-key'].splitlines()
        else:
            fieldkeys = defaultKeys(options['blueprint'], name, 'field')
        self.fieldkey = Matcher(*fieldkeys)

    def __iter__(self):
        for item in self.previous:
            pathkey = self.pathkey(*item.keys())[0]
            if not pathkey:
                yield item; continue

            criterionkey = self.criterionkey(*item.keys())[0]
            if not criterionkey:
                yield item; continue

            fieldkey = self.fieldkey(*item.keys())[0]
            if not fieldkey:
                yield item; continue

            path = item[pathkey]

            obj = self.context.unrestrictedTraverse(path.lstrip('/'), None)
            if obj is None:         # path doesn't exist
                yield item; continue

            criterion = item[criterionkey]
            field = item[fieldkey]

            if IATTopic.providedBy(obj):
                critid = 'crit__%s_%s' % (field, criterion)
                if getattr(aq_base(obj), critid, None) is None:
                    obj.addCriterion(field, criterion)
                item[pathkey] = '%s/%s' % (path, critid)

            yield item
