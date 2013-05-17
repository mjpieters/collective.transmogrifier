import os
import posixpath

from zope.interface import classProvides, implements
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.interfaces import ISection

from collective.transmogrifier.utils import resolvePackageReferenceOrFile
from collective.transmogrifier.utils import Expression


class DirWalkerSection(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.pathkey = options.get('path-key', '_path')
        self.typekey = options.get('type-key', '_type')
        self.foldertype = options.get('folder-type', 'Folder')
        self.dirname = options['dirname'] = resolvePackageReferenceOrFile(
            options['dirname'])
        self.sortkey = Expression(
            options.get('sort-key',
                        "python:not basename.lower() == '.htaccess', "
                        "not basename.lower().startswith('index'), "
                        "not 'overview' in basename.lower(), basename"),
            transmogrifier, name, options)

    def __iter__(self):
        for item in self.previous:
            yield item

        cwd = os.getcwd()
        yield {self.pathkey: posixpath.sep,
               self.typekey: self.foldertype}

        try:
            os.chdir(self.dirname)
            for (dirpath, dirnames, filenames) in os.walk(os.curdir):
                os.chdir(cwd)

                def sortkey(basename, dirpath=dirpath, sortkey=self.sortkey):
                    return sortkey({}, dirpath=dirpath, basename=basename)

                for basename in sorted(filenames, key=sortkey):
                    yield {self.pathkey: posixpath.relpath(
                        posixpath.join(posixpath.sep, dirpath, basename),
                        posixpath.sep)}
                for basename in sorted(dirnames, key=sortkey):
                    yield {
                        self.pathkey: posixpath.relpath(
                            posixpath.join(posixpath.sep, dirpath, basename),
                            posixpath.sep) + posixpath.sep,
                        self.typekey: self.foldertype}

                os.chdir(self.dirname)

        finally:
            os.chdir(cwd)
