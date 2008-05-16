from zope import event
from zope.interface import classProvides, implements
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.utils import Matcher
from collective.transmogrifier.utils import defaultKeys

from Products.Archetypes.interfaces import IBaseObject
from Products.Archetypes.event import ObjectInitializedEvent
from Products.Archetypes.event import ObjectEditedEvent

class ATSchemaUpdaterSection(object):
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
    
    def __iter__(self):
        for item in self.previous:
            pathkey = self.pathkey(*item.keys())[0]
            
            if not pathkey:         # not enough info
                yield item; continue
            
            path = item[pathkey]
            
            obj = self.context.unrestrictedTraverse(path.lstrip('/'), None)
            if obj is None:         # path doesn't exist
                yield item; continue
            
            if IBaseObject.providedBy(obj):
                is_new_object = obj.checkCreationFlag()
                obj.update(**dict((k,v) for k,v in item.iteritems() 
                                  if k[0:1] != '_'))
                obj.unmarkCreationFlag()
                if is_new_object:
                    event.notify(ObjectInitializedEvent(obj))
                    obj.at_post_create_script()
                else:
                    event.notify(ObjectEditedEvent(obj))
                    obj.at_post_edit_script()
            
            yield item
