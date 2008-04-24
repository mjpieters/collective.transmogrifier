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
        
        if 'path-key' in options:
            pathkeys = options['path-key'].splitlines()
        else:
            pathkeys = defaultKeys(options['blueprint'], name, 'path')
        self.pathkey = Matcher(*pathkeys)
    
    def __iter__(self):
        for item in self.previous:
            pathkey = self.pathkey(*item.keys())[0]
            
            if not pathkey:         # not enough info
                yield item; continue
            
            path = item[pathkey]
            if isinstance(path, unicode):
                path = path.encode('ascii')
            
            obj = self.portal.unrestrictedTraverse(path.lstrip('/'), None)
            if obj is None:         # path doesn't exist
                yield item; continue
            
            if IBaseObject.providedBy(obj):
                obj.update(**dict((k,v) for k,v in item.iteritems() 
                                  if k[0:1] != '_'))
            
            yield item
