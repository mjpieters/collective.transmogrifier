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
        if self.filename:
            self.filename = options['filename'] = (
                resolvePackageReferenceOrFile(self.filename))

        self.rowkey = options.get('row-key')
        if 'row-key' in options:
            self.rowkey = Expression(
                self.rowkey, transmogrifier, name, options)
            self.rowvalue = Expression(
                options.get('row-value', 'filename'),
                transmogrifier, name, options)

        self.dialect = options.get('dialect', 'excel')
        self.restkey = options.get('restkey', '_csvsource_rest')
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

            filename = resolvePackageReferenceOrFile(item[key])
            for row_item in self.rows(filename):
                if self.rowkey:
                    rowkey = self.rowkey(
                        row_item, filename=filename, source_item=item)
                    if rowkey:
                        row_item[rowkey] = self.rowvalue(
                            row_item, filename=filename, source_item=item)
                yield row_item

        if self.filename:
            for item in self.rows(self.filename):
                yield item

    def rows(self, filename):
        if os.path.isfile(filename):
            file_ = open(filename, 'r')
            reader = csv.DictReader(
                file_, dialect=self.dialect,
                fieldnames=self.fieldnames, restkey=self.restkey,
                **self.fmtparam)
            for item in reader:
                yield item
