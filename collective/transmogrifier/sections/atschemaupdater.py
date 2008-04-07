from zope.interface import classProvides, implements
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.utils import Matcher
from collective.transmogrifier.utils import defaultKeys

from Products.Archetypes.interfaces import IBaseObject

class ATSchemaUpdaterSection(object):
    classProvides(ISectionBlueprint)
    implements(ISection)
    
    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.portal = transmogrifier.portal
        
        if 'id-key' in options:
            idkeys = options['id-key'].splitlines()
        else:
            idkeys = defaultKeys(options['blueprint'], name, 'id')
            idkeys += ('getId', 'id')
        self.idkey = Matcher(*idkeys)
        
        if 'path-key' in options:
            pathkeys = options['type-key'].splitlines()
        else:
            pathkeys = defaultKeys(options['blueprint'], name, 'path')
        self.pathkey = Matcher(*pathkeys)
    
    def __iter__(self):
        for item in self.previous:
            keys = item.keys()
            idkey = self.idkey(*keys)[0]
            pathkey = self.pathkey(*keys)[0]
            
            if not (idkey and pathkey): # not enough info
                yield item; continue
            
            id, path = item[idkey], item[pathkey]
            
            while path[0] == '/': path = path[1:]
            context = self.portal.unrestrictedTraverse(path, None)
            if context is None:         # path doesn't exist
                yield item; continue
            
            obj = getattr(context, id, None)
            if obj is None:             # item does not exist
                yield item; continue
            
            if IBaseObject.providedBy(obj):
                for field in obj.Schema().editableFields():
                    if not field.getName() in item:
                        continue
                    setter = field.getMutator(obj)
                    if setter is not None:
                        setter(item[field.getName()])
            
            yield item
