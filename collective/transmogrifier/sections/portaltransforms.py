from zope.interface import classProvides, implements
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.utils import Matcher, Condition

from Products.CMFCore.utils import getToolByName

class PortalTransformsSection(object):
    classProvides(ISectionBlueprint)
    implements(ISection)
    
    def __init__(self, transmogrifier, name, options, previous):
        self.ptransforms = getToolByName(transmogrifier.context,
                                         'portal_transforms')
        self.keys = Matcher(*options['keys'].splitlines())
        self.transform = options.get('transform')
        if not self.transform:
            self.target = options['target']
            self.from_ = options.get('from')
        self.condition = Condition(options.get('condition', 'python:True'),
                                   transmogrifier, name, options)
        self.previous = previous
    
    def __iter__(self):
        for item in self.previous:
            for key in item:
                match = self.keys(key)[1]
                if not (match and self.condition(item, key=key, match=match)):
                    continue
                if self.transform:
                    item[key] = self.ptransforms(self.transform, item[key])
                else:
                    item[key] = self.ptransforms.convertToData(
                        self.target, item[key], mimetype=self.from_)
            yield item
