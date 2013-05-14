import os
import csv

from zope.interface import classProvides, implements
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.interfaces import ISection

from collective.transmogrifier.utils import resolvePackageReferenceOrFile
from collective.transmogrifier.utils import defaultMatcher
from collective.transmogrifier.utils import Expression


class CSVSourceSection(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous

        self.key = defaultMatcher(options, 'key', name)
        self.filename = options.get('filename')
        self.filenamekey = options.get('filename-key', '_csvsource')
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

            key = self.key(*item)[0]
            if not key:
                continue

            filename = item[key]
            for new_item in self.rows(filename):
                if self.filenamekey:
                    new_item[self.filenamekey] = filename
                yield new_item

        if self.filename:
            for item in self.rows(self.filename):
                yield item

    def rows(self, filename):
        filename = resolvePackageReferenceOrFile(filename)
        if os.path.isfile(filename):
            file_ = open(filename, 'r')
            reader = csv.DictReader(
                file_, dialect=self.dialect, fieldnames=self.fieldnames,
                **self.fmtparam)
            for item in reader:
                yield item
