import itertools
import collections

from zope.interface import classProvides, implements

from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.interfaces import ISection

# Note that this implementation simply uses itertools.tee, which means that it
# will become a memory hog if one pipe condition doesn't much anything for a
# lot of items.
#
# The solution is to use co-routines (PEP 342), something not available until
# python 2.5. Alternatively this could possibly be solved using threads, which
# would mean that all sub-pipes would be in the wrong thread to access
# transmogrifier.portal, with all that entails.
#
# A complex solution that minimizes the memory problem is to look ahead at
# the next item in the previous section and pre-select sub-pipes on that
# basis. The complexity comes into play when sub-pipes start discarding
# items and/or injecting extra. This would probably require a custom
# tee function that let's us peek at the buffer and detect when a sub-pipe
# did not pull from the pipe head when it advanced.

class SplitterSection(object):
    classProvides(ISectionBlueprint)
    implements(ISectionBlueprint)
    
    def __init__(self, transmogrifier, name, options, previous):
        self.subpipes = collections.deque()
        
        pipe_ids = [k for k in options if k.startswith('pipeline')]
        pipe_ids.sort()
        
        splitter_head = list(itertools.tee(previous, len(pipe_ids)))
        
        for pipe_id, pipeline in zip(pipe_ids, splitter_head):
            condition = options.get('%s-condition' % pipe_id)
            if contition is not None:
                # TODO: insert condition section.
                pass
            
            sections = [s.strip() for s in options[pipe_id].split() 
                        if s.strip()]
            # Pipeline construction
            for section_id in sections:
                section_options = transmogrifier[section_id]
                blueprint_id = section_options['blueprint'].decode('ascii')
                blueprint = getUtility(ISectionBlueprint, blueprint_id)
                pipeline = blueprint(self, section_id, section_options,
                                     pipeline)
                if not ISection.providedBy(pipeline):
                    raise ValueError('Blueprint %s for section %s did not '
                                     'return an ISection' % (
                                          blueprint_id, section_id))
                pipeline = iter(pipeline)
                
            self.subpipes.appendleft(pipeline)
    
    def __iter__(self):
        subpipes = self.subpipes
        while subpipes:
            try:
                yield subpipes[-1].next()
            except StopIteration:
                subpipes.pop()
            else:
                subpipes.rotate()
