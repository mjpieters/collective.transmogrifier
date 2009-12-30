import csv
from zope.interface import classProvides, implements
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.interfaces import ISection

from collective.transmogrifier.utils import resolvePackageReferenceOrFile

class CSVSourceSection(object):
    classProvides(ISectionBlueprint)
    implements(ISection)
    
    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        
        filename = resolvePackageReferenceOrFile(options['filename'])
        file_ = open(filename, 'r')
        dialect = options.get('dialect', 'excel')
        fieldnames = options.get('fieldnames')
        if fieldnames:
            fieldnames = fieldnames.split()
        
        self.reader = csv.DictReader(file_, 
            dialect=dialect, fieldnames=fieldnames)
    
    def __iter__(self):
        for item in self.previous:
            yield item
        
        for item in self.reader:
            yield item
