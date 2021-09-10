# -*- coding: utf-8 -*-
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.utils import defaultMatcher
from collective.transmogrifier.utils import Expression
from collective.transmogrifier.utils import openFileReference
from zope.interface import provider
from zope.interface import implementer

import csv


@provider(ISectionBlueprint)
@implementer(ISection)
class CSVSourceSection(object):
    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.transmogrifier = transmogrifier

        self.key = defaultMatcher(options, "key", name)
        self.filename = options.get("filename")
        if self.filename:
            self.filename = options["filename"] = self.filename

        self.rowkey = options.get("row-key")
        if "row-key" in options:
            self.rowkey = Expression(self.rowkey, transmogrifier, name, options)
            self.rowvalue = Expression(
                options.get("row-value", "filename"), transmogrifier, name, options
            )

        self.dialect = options.get("dialect", "excel")
        self.restkey = options.get("restkey", "_csvsource_rest")
        self.fmtparam = dict(
            (
                key[len("fmtparam-"):],
                Expression(value, transmogrifier, name, options)(
                    options, key=key[len("fmtparam-"):]
                ),
            )
            for key, value in options.items()
            if key.startswith("fmtparam-")
        )
        self.fieldnames = options.get("fieldnames")
        if self.fieldnames:
            self.fieldnames = self.fieldnames.split()

    def __iter__(self):
        for item in self.previous:
            yield item

            key = self.key(*item)[0]
            if not key:
                continue

            for row_item in self.rows(item[key]):
                if self.rowkey:
                    rowkey = self.rowkey(row_item, filename=item[key], source_item=item)
                    if rowkey:
                        row_item[rowkey] = self.rowvalue(
                            row_item, filename=item[key], source_item=item
                        )
                yield row_item

        if self.filename:
            for item in self.rows(self.filename):
                yield item

    def rows(self, filename):
        file_ = openFileReference(self.transmogrifier, filename)
        if file_ is None:
            return
        reader = csv.DictReader(
            file_,
            dialect=self.dialect,
            fieldnames=self.fieldnames,
            restkey=self.restkey,
            **self.fmtparam
        )
        for item in reader:
            yield item
        file_.close()
