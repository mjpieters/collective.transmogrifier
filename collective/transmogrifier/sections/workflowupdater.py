from zope.interface import classProvides, implements
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.utils import Matcher
from collective.transmogrifier.utils import defaultKeys

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.WorkflowCore import WorkflowException

class WorkflowUpdaterSection(object):
    classProvides(ISectionBlueprint)
    implements(ISection)
    
    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.portal = transmogrifier.portal
        self.wftool = getToolByName(self.portal, 'portal_workflow')
        
        if 'path-key' in options:
            pathkeys = options['type-key'].splitlines()
        else:
            pathkeys = defaultKeys(options['blueprint'], name, 'path')
        self.pathkey = Matcher(*pathkeys)
        
        if 'transitions-key' in options:
            transitionskeys = options['transitions-key'].splitlines()
        else:
            transitionskeys = defaultKeys(options['blueprint'], name, 
                                           'transitions')
        self.transitionskey = Matcher(*transitionskeys)
    
    def __iter__(self):
        for item in self.previous:
            keys = item.keys()
            pathkey = self.pathkey(*keys)[0]
            transitionskey = self.transitionskey(*keys)[0]
            
            if not (pathkey and transitionskey): # not enough info
                yield item; continue
            
            path, transitions = item[pathkey], item[transitionskey]
            if isinstance(transitions, basestring):
                transitions = (transitions,)
            if isinstance(path, unicode):
                path = path.encode('ascii')
            
            obj = self.portal.unrestrictedTraverse(path.lstrip('/'), None)
            if obj is None:                      # path doesn't exist
                yield item; continue
            
            for transition in transitions:
                try:
                    self.wftool.doActionFor(obj, transition)
                except WorkflowException:
                    pass
            
            yield item
