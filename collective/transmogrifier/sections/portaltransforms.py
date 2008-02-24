from zope.interface import classProvides, implements
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.utils import Matcher

from Products.CMFCore.utils import getToolByName

class PortalTransformsSection(object):
    classProvides(ISectionBlueprint)
    implements(ISection)
    
    def __init__(self, transmogrifier, name, options, previous):
        self.ptransforms = getToolByName(transmogrifier.portal,
                                         'portal_transforms')
        self.keys = Matcher(options['keys'].splitlines())
        self.transform = options.get('transform')
        if self.transform is None:
            self.target = options['target']
            self.from_ = options.get('from')
        self.previous = previous
    
    def __iter__(self):
        for item in self.previous:
            for key in item:
                if not self.keys(key):
                    continue
                if self.transform is not None:
                    item[key] = self.ptransforms(self.transform, item[key])
                else:
                    item[key] = self.ptransforms.convertToData(
                        self.target, item[key], mimetype=self.from_)
            yield item
