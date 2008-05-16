from zope.interface import classProvides, implements
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.utils import defaultMatcher

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.WorkflowCore import WorkflowException

class WorkflowUpdaterSection(object):
    classProvides(ISectionBlueprint)
    implements(ISection)
    
    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.context = transmogrifier.context
        self.wftool = getToolByName(self.context, 'portal_workflow')
        
        self.pathkey = defaultMatcher(options, 'path-key', name, 'path')
        self.transitionskey = defaultMatcher(options, 'transitions-key', name,
                                             'transitions')
    
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
            
            obj = self.context.unrestrictedTraverse(path.lstrip('/'), None)
            if obj is None:                      # path doesn't exist
                yield item; continue
            
            for transition in transitions:
                try:
                    self.wftool.doActionFor(obj, transition)
                except WorkflowException:
                    pass
            
            yield item
