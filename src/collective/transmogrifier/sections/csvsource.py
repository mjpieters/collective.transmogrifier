import csv
from zope.interface import classProvides, implements
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.interfaces import ISection

from collective.transmogrifier.utils import resolvePackageReferenceOrFile
from collective.transmogrifier.utils import Expression


class CSVSourceSection(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous

        self.key = options.get('key')
        if self.key:
            self.key = Expression(self.key, transmogrifier, name, options)
        self.filename = options.get('filename')
        self.dialect = options.get('dialect', 'excel')
        self.fmtparam = dict(
            (key[len('fmtparam-'):],
             Expression(value, transmogrifier, name, options)(
                 options, key=key[len('fmtparam-'):])) for key, value
            in options.iteritems() if key.startswith('fmtparam-'))
        self.fieldnames = options.get('fieldnames')
        if self.fieldnames:
            self.fieldnames = self.fieldnames.split()

    def __iter__(self):
        for item in self.previous:
            yield item

            if self.key:
                filename = self.key(item)
                if filename:
                    for item in self.rows(filename):
                        yield item

        if self.filename:
            for item in self.rows(self.filename):
                yield item

    def rows(self, filename):
        filename = resolvePackageReferenceOrFile(filename)
        file_ = open(filename, 'r')
        reader = csv.DictReader(
            file_, dialect=self.dialect, fieldnames=self.fieldnames,
            **self.fmtparam)
        for item in reader:
            yield item
