from zope.interface import classProvides, implements
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.utils import defaultMatcher

class FoldersSection(object):
    classProvides(ISectionBlueprint)
    implements(ISection)
    
    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.context = transmogrifier.context
        
        self.pathKey = defaultMatcher(options, 'path-key', name, 'path')
        
        self.newPathKey = options.get('new-path-key', None)
        self.newTypeKey = options.get('new-type-key', '_type')
        
        self.folderType = options.get('folder-type', 'Folder')
        self.cache      = options.get('cache', 'true').lower() == 'true'
        
        self.seen       = set()
    
    def __iter__(self):
        
        for item in self.previous:
            
            keys = item.keys()
            pathKey = self.pathKey(*keys)[0]
            
            if not pathKey: # not enough info
                yield item; continue
            
            newPathKey = self.newPathKey or pathKey
            newTypeKey = self.newTypeKey
            
            path = item[pathKey]
            elems = path.strip('/').rsplit('/', 1)
            container, id = (len(elems) == 1 and ('', elems[0]) or elems)
            
            traverse = self.context.unrestrictedTraverse
            
            # This may be a new container
            if container not in self.seen:
                
                containerPathItems = container.split('/')
                if containerPathItems:
                    
                    checkedElements = []
                
                    # Check each possible parent folder
                    for element in containerPathItems:
                        checkedElements.append(element)
                        currentPath = '/'.join(checkedElements)
                    
                        if currentPath and currentPath not in self.seen:
                        
                            if traverse(currentPath, None) is None:
                                # We don't have this path - yield to create a
                                # skeleton folder
                                yield {newPathKey: '/' + currentPath,
                                       newTypeKey: self.folderType}
                        
                            if self.cache:
                                self.seen.add(currentPath)
            
            if self.cache:
                self.seen.add("%s/%s" % (container, id,))
            
            yield item
