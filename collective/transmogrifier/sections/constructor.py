from zope.interface import classProvides, implements
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.utils import Matcher
from collective.transmogrifier.utils import defaultKeys

from Products.CMFCore.utils import getToolByName

class ConstructorSection(object):
    classProvides(ISectionBlueprint)
    implements(ISection)
    
    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.portal = transmogrifier.portal
        self.ttool = getToolByName(self.portal, 'portal_types')
        
        if 'id-key' in options:
            idkeys = options['id-key'].splitlines()
        else:
            idkeys = defaultKeys(options['blueprint'], name, 'id')
            idkeys += ('getId', 'id')
        self.idkey = Matcher(*idkeys)
        
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
            
            while path[0] == '/': path = path[1:]
            while path[-1] == '/': path = path[:-1]
            container, id = path.rsplit('/', 1)
            context = self.portal.unrestrictedTraverse(container, None)
            if context is None:                        # container doesn't exist
                yield item; continue
            
            if getattr(context, id, None) is not None: # item exists
                yield item; continue
            
            new_id = context.invokeFactory(id=id, type_name=type_)
            if new_id and new_id != id:
                item[pathkey] = '%s/%s' % (container, new_id)
            
            yield item
