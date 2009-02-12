import itertools
import collections
import copy

from zope.interface import classProvides, implements

from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.utils import constructPipeline
from collective.transmogrifier.utils import Condition

# This splitter uses look-ahead condition sections to only advance sub-pipes
# that can actually yield something, thus avoiding filling the itertools.tee
# buffer while one of the conditions continues not to match. We go to some
# pain to avoid having extra items stuck in the pipes, or to empty the
# itertools.tee buffer if it does fill.
#
# Every time one of the sub-pipes themselves discard items though,
# theoretically the sub-pipe could pull in *all* remaining pipeline items, at
# least until one item is found that matches the sub-pipe condition. This will
# of course quickly fill the itertools.tee buffer and become a memory problem.
#
# A better solution would be to use co-routines (PEP 342), something not
# available until python 2.5. Alternatively this could possibly be solved
# using threads, which would mean that all sub-pipes would be in the wrong
# thread to access transmogrifier.context, with all that entails.

# Unique marker tokens for the look-ahead buffer
_empty = []
_stop = []

class SplitterConditionSection(object):
    implements(ISection)
    
    # how far ahead are we
    ahead = 0
    
    def __init__(self, condition, previous):
        self.condition = condition or (lambda x: True)
        self.previous = previous
        self._buffer = _empty
        
    def __iter__(self):
        return self
        
    def next(self):
        self.ahead += 1
        
        while True:
            if self._buffer is _stop:
                raise StopIteration
        
            if self._buffer is not _empty:
                next = self._buffer
                self._buffer = _empty
            else:
                next = self.previous.next()
            
            if self.condition(next):
                return copy.deepcopy(next)
        
    @property
    def isAhead(self):
        """Are we ahead?
        
        If we are, decrease the ahead counter every time we test.
        
        """
        isAhead = self.ahead > 0
        if isAhead:
            self.ahead -= 1
        return isAhead
    
    def _getBuffer(self):
        if self._buffer is _empty:
            try:
                self._buffer = self.previous.next()
            except StopIteration:
                self._buffer = _stop
        return self._buffer
        
    @property
    def willMatch(self):
        """Condition will match the next item from self.previous
        
        Not matching items are discarded.
        
        """
        next = self._getBuffer()
        if next is _stop:
            return False
        
        if not self.condition(next):
            # Won't match, discard buffer. We'll advance again when tested
            # again or if self.next() is called.
            self._buffer = _empty
            return False
            
        return True
    
    @property
    def isDone(self):
        return self._getBuffer() is _stop


class SplitterSection(object):
    classProvides(ISectionBlueprint)
    implements(ISection)
    
    def __init__(self, transmogrifier, name, options, previous):
        self.subpipes = collections.deque()
        
        pipe_ids = [k for k in options
                    if k.startswith('pipeline-') and 
                       not k.endswith('-condition')]
        pipe_ids.sort()
        
        if len(pipe_ids) < 2:
            raise ValueError(
                '%s: Need at least two sub-pipes for a splitter' % name)
        
        splitter_head = list(itertools.tee(previous, len(pipe_ids)))
        
        for pipe_id, pipeline in zip(pipe_ids, splitter_head):
            condition = options.get('%s-condition' % pipe_id)
            if condition:
                condition = Condition(condition, transmogrifier, name, 
                                      options, pipeline=pipe_id)
            condition = SplitterConditionSection(condition, pipeline)
            
            sections = options[pipe_id].splitlines() 
            pipeline = constructPipeline(transmogrifier, sections, condition)
            self.subpipes.appendleft((condition, pipeline))
    
    def __iter__(self):
        subpipes = self.subpipes
        while subpipes:
            try:
                condition, pipe = subpipes[-1]
                
                if condition.isAhead:
                    # This sub-pipe is ahead, skip until the itertools.tee
                    # buffer has caught up again
                    subpipes.rotate()
                    continue
                
                if condition.willMatch:
                    yield pipe.next()
                    while not condition.isAhead:
                        # pipe is inserting extra items, advance until
                        # item in condition section has been used
                        yield pipe.next()
                
                while condition.isDone:
                    # self.previous is done, but perhaps not the sub-pipe
                    yield pipe.next()
            except StopIteration:
                subpipes.pop()
            else:
                subpipes.rotate()
