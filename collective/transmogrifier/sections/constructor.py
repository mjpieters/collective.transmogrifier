from zope.interface import classProvides, implements
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.utils import Matcher
from collective.transmogrifier.utils import defaultKeys

class ConstructorSection(object):
    classProvides(ISectionBlueprint)
    implements(ISection)
    
    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        
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
