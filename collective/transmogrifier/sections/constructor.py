from zope.interface import classProvides, implements
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.utils import Matcher
from collective.transmogrifier.utils import defaultKeys

from Acquisition import aq_base
from Products.CMFCore.utils import getToolByName

class ConstructorSection(object):
    classProvides(ISectionBlueprint)
    implements(ISection)
    
    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.portal = transmogrifier.portal
        self.ttool = getToolByName(self.portal, 'portal_types')
        
        if 'type-key' in options:
            typekeys = options['type-key'].splitlines()
        else:
            typekeys = defaultKeys(options['blueprint'], name, 'type')
            typekeys += ('portal_type', 'Type')
        self.typekey = Matcher(*typekeys)
        
        if 'path-key' in options:
            pathkeys = options['type-key'].splitlines()
        else:
            pathkeys = defaultKeys(options['blueprint'], name, 'path')
        self.pathkey = Matcher(*pathkeys)
    
    def __iter__(self):
        for item in self.previous:
            keys = item.keys()
            typekey = self.typekey(*keys)[0]
            pathkey = self.pathkey(*keys)[0]
            
            if not (typekey and pathkey):              # not enough info
                yield item; continue
            
            type_, path = item[typekey], item[pathkey]
            
            if self.ttool.getTypeInfo(type_) is None:  # not an existing type
                yield item; continue
            
            elems = path.strip('/').rsplit('/', 1)
            container, id = (len(elems) == 1 and ('', elems[0]) or elems)
            context = self.portal.unrestrictedTraverse(container, None)
            if context is None:                        # container doesn't exist
                yield item; continue
            
            if getattr(aq_base(context), id, None) is not None: # item exists
                yield item; continue
            
            new_id = context.invokeFactory(id=id, type_name=type_)
            if new_id and new_id != id:
                item[pathkey] = '%s/%s' % (container, new_id)
            
            yield item
