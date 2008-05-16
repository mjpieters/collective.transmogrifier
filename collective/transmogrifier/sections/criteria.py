from zope.interface import classProvides, implements
from zope.component import queryUtility

from collective.transmogrifier.interfaces import ISection, ISectionBlueprint
from collective.transmogrifier.utils import defaultMatcher

from Acquisition import aq_base
from Products.ATContentTypes.interface import IATTopic


class CriterionAdder(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.context = transmogrifier.context

        self.pathkey = defaultMatcher(options, 'path-key', name, 'path')
        self.criterionkey = defaultMatcher(options, 'criterion-key', name,
                                           'criterion')
        self.fieldkey = defaultMatcher(options, 'field-key', name, 'field')

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
