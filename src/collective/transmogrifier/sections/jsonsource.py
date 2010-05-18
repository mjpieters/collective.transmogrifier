import os
import simplejson
from zope.interface import classProvides, implements
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.interfaces import ISection

from collective.transmogrifier.utils import resolvePackageReferenceOrFile

class JSONSourceSection(object):
    classProvides(ISectionBlueprint)
    implements(ISection)
    
    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        
        self.path = resolvePackageReferenceOrFile(options['path'])
        if self.path is None and not os.path.isdir(self.path):
            raise Exception, 'Path ('+str(self.path)+') does not exists.'
    
    def __iter__(self):
        for item in self.previous:
            yield item

        for item in sorted([int(i)
                                for i in os.listdir(self.path)
                                    if not i.startswith('.')]):

            for item2 in sorted([int(j[:-5])
                                    for j in os.listdir(os.path.join(self.path, str(item)))
                                        if j.endswith('.json')]):

                f = open(os.path.join(self.path, str(item), str(item2)+'.json'))
                item3 = simplejson.loads(f.read())
                f.close()

                yield item3

