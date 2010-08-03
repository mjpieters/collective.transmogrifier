import logging

from zope.interface import classProvides, implements

from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.interfaces import ISection

# Logs a value of a key.

class LoggerSection(object):
    classProvides(ISectionBlueprint)
    implements(ISection)
    
    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        
        # First check if the level is a named level:
        self.level = getattr(logging, options['level'], None)
        if self.level is None:
            # Assume it's an integer:
            self.level = int(options['level'])

        self.logger = logging.getLogger(options['name'])
        self.logger.setLevel(self.level)
        self.key = options['key']
    
    def __iter__(self):
        for item in self.previous:
            self.logger.log(self.level, item.get(self.key, '-- Missing key --'))
            yield item
