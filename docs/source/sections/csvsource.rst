CSV source section
==================

A CSV source pipeline section lets you create pipeline items from CSV files.
The CSV source section blueprint name is
``collective.transmogrifier.sections.csvsource``.

A CSV source section will load the CSV file named in the ``filename``
option or the CSV file named in an item key using the ``key`` option,
and will yield an item for each line in the CSV file. It'll use the first line
of the CSV file to determine what keys to use, or you can specify a
``fieldnames`` option to specify the key names.

The ``filename`` option may be an absolute path, or a package reference, e.g.
``my.package:foo/bar.csv``.

By default the CSV file is assumed to use the Excel CSV dialect, but you can
specify any dialect supported by the python csv module if you specify it with
the ``dialect`` option.  You can also specify `fmtparams`_ using
options that start with ``fmtparam-``.


    >>> import os
    >>> from collective.transmogrifier import tests
    >>> csvsource = """
    ... [transmogrifier]
    ... pipeline =
    ...     csvsource
    ...     logger
    ...
    ... [csvsource]
    ... blueprint = collective.transmogrifier.sections.csvsource
    ... filename = {}/csvsource.csv
    ...
    ... [logger]
    ... blueprint = collective.transmogrifier.sections.logger
    ... name = logger
    ... level = INFO
    ... """.format(os.path.dirname(tests.__file__))
    >>> registerConfig('collective.transmogrifier.sections.tests.csvsource.file',
    ...                csvsource)
    >>> transmogrifier('collective.transmogrifier.sections.tests.csvsource.file')
    >>> print(handler)
    logger INFO
        {'bar': 'first-bar', 'baz': 'first-baz', 'foo': 'first-foo'}
    logger INFO
        {'bar': 'second-bar', 'baz': 'second-baz', 'foo': 'second-foo'}

The CSV file column field names can also be specified.

    >>> handler.clear()
    >>> transmogrifier('collective.transmogrifier.sections.tests.csvsource.file',
    ...                csvsource=dict(fieldnames='monty spam eggs'))
    >>> print(handler)
    logger INFO
        {'eggs': 'baz', 'monty': 'foo', 'spam': 'bar'}
    logger INFO
        {'eggs': 'first-baz', 'monty': 'first-foo', 'spam': 'first-bar'}
    logger INFO
        {'eggs': 'second-baz', 'monty': 'second-foo', 'spam': 'second-bar'}

Here is the same example, loading a file from a package instead:

    >>> csvsource = """
    ... [transmogrifier]
    ... pipeline =
    ...     csvsource
    ...     logger
    ...
    ... [csvsource]
    ... blueprint = collective.transmogrifier.sections.csvsource
    ... filename = collective.transmogrifier.tests:sample.csv
    ...
    ... [logger]
    ... blueprint = collective.transmogrifier.sections.logger
    ... name = logger
    ... level = INFO
    ... """
    >>> registerConfig('collective.transmogrifier.sections.tests.csvsource.package',
    ...                csvsource)
    >>> handler.clear()
    >>> transmogrifier('collective.transmogrifier.sections.tests.csvsource.package')
    >>> print(handler)
    logger INFO
        {'bar': 'first-bar', 'baz': 'first-baz', 'foo': 'first-foo'}
    logger INFO
        {'_csvsource_rest': ['corge', 'grault'],
       'bar': 'second-bar',
       'baz': 'second-baz',
       'foo': 'second-foo'}

We can also load a file from a GS import context:

    >>> from collective.transmogrifier.transmogrifier import Transmogrifier
    >>> from collective.transmogrifier.genericsetup import IMPORT_CONTEXT
    >>> from zope.annotation.interfaces import IAnnotations
    >>> class FakeImportContext(object):
    ...  def __init__(self, subdir, filename, contents):
    ...      self.filename = filename
    ...      self.subdir = subdir
    ...      self.contents = contents
    ...  def readDataFile(self, filename, subdir=None):
    ...      if subdir is None and self.subdir is not None:
    ...          return None
    ...      if filename != self.filename:
    ...          return None
    ...      return self.contents
    >>> csvsource = """
    ... [transmogrifier]
    ... pipeline =
    ...     csvsource
    ...     logger
    ...
    ... [csvsource]
    ... blueprint = collective.transmogrifier.sections.csvsource
    ... filename = importcontext:sub/dir/somefile.csv
    ...
    ... [logger]
    ... blueprint = collective.transmogrifier.sections.logger
    ... name = logger
    ... level = INFO
    ... """
    >>> registerConfig('collective.transmogrifier.sections.tests.csvsource.gs',
    ...                csvsource)
    >>> handler.clear()
    >>> t = Transmogrifier({})
    >>> IAnnotations(t)[IMPORT_CONTEXT] = FakeImportContext('sub/dir/', 'somefile.csv',
    ... """animal,name
    ... cow,daisy
    ... pig,george
    ... duck,archibald
    ... """)
    >>> t('collective.transmogrifier.sections.tests.csvsource.gs')
    >>> print(handler)
    logger INFO
        {'animal': 'cow', 'name': 'daisy'}
    logger INFO
        {'animal': 'pig', 'name': 'george'}
    logger INFO
        {'animal': 'duck', 'name': 'archibald'}

Import contexts can be chunked, and that's okay:

    >>> import six
    >>> class FakeChunkedImportContext(object):
    ...  def __init__(self, subdir, filename, contents):
    ...      self.filename = filename
    ...      self.contents = contents
    ...  def openDataFile(self, filename, subdir=None):
    ...      if subdir is None and self.subdir is not None:
    ...          return None
    ...      if filename != self.filename:
    ...          return None
    ...      return six.StringIO(self.contents)
    >>> handler.clear()
    >>> t = Transmogrifier({})
    >>> IAnnotations(t)[IMPORT_CONTEXT] = FakeChunkedImportContext(None, 'somefile.csv',
    ... """animal,name
    ... fish,wanda
    ... """)
    >>> t('collective.transmogrifier.sections.tests.csvsource.gs')
    >>> print(handler)
    logger INFO
        {'animal': 'fish', 'name': 'wanda'}

Attempting to load a nonexistant file won't do anything:

    >>> handler.clear()
    >>> t = Transmogrifier({})
    >>> IAnnotations(t)[IMPORT_CONTEXT] = FakeImportContext(None, 'someotherfile.csv',
    ... """animal,name
    ... cow,daisy
    ... pig,george
    ... duck,archibald
    ... """)
    >>> t('collective.transmogrifier.sections.tests.csvsource.gs')
    >>> print(handler)

Not having an import context around will also find nothing:

    >>> handler.clear()
    >>> t = Transmogrifier({})
    >>> t('collective.transmogrifier.sections.tests.csvsource.gs')
    >>> print(handler)

The file can also be taken from a source item's key. A key can also be
specified for rows that have more values than the fieldnames.

    >>> csvsource = """
    ... [transmogrifier]
    ... include = collective.transmogrifier.sections.tests.csvsource.package
    ... pipeline =
    ...     csvsource
    ...     filename
    ...     item-csvsource
    ...     logger
    ...
    ... [csvsource]
    ... blueprint = collective.transmogrifier.sections.csvsource
    ... filename = collective.transmogrifier.tests:keysource.csv
    ...
    ... [filename]
    ... blueprint = collective.transmogrifier.sections.inserter
    ... key = string:_item-csvsource
    ... condition = exists:item/_item-csvsource
    ... value = python:modules['os.path'].join(modules['os.path'].dirname(
    ...     modules['collective.transmogrifier.tests'].__file__),
    ...     item['_item-csvsource'])
    ...
    ... [item-csvsource]
    ... blueprint = collective.transmogrifier.sections.csvsource
    ... restkey = _args
    ... row-key = string:_csvsource
    ...
    ... """
    >>> registerConfig('collective.transmogrifier.sections.tests.csvsource.key',
    ...                csvsource)

    >>> handler.clear()
    >>> transmogrifier('collective.transmogrifier.sections.tests.csvsource.key')
    >>> print(handler)
    logger INFO
        {'_item-csvsource': '.../collective/transmogrifier/tests/sample.csv'}
    logger INFO
        {'_csvsource': '.../collective/transmogrifier/tests/sample.csv',
       'bar': 'first-bar',
       'baz': 'first-baz',
       'foo': 'first-foo'}
    logger INFO
        {'_args': ['corge', 'grault'],
       '_csvsource': '.../collective/transmogrifier/tests/sample.csv',
       'bar': 'second-bar',
       'baz': 'second-baz',
       'foo': 'second-foo'}

The ``fmtparam-`` expressions have access to the following:

=================== ==========================================================
 ``key``             the `fmtparam`_ attribute
 ``transmogrifier``  the transmogrifier
 ``name``            the name of the inserter section
 ``options``         the inserter options
 ``modules``         sys.modules
=================== ==========================================================

The ``row-key`` and ``row-value`` expressions have access to the following:

=================== ==========================================================
 ``item``            the pipeline item to be yielded from this CSV row
 ``source_item``     the pipeline item the CSV filename was taken from
 ``transmogrifier``  the transmogrifier
 ``name``            the name of the inserter section
 ``options``         the inserter options
 ``modules``         sys.modules
 ``key``             (only for the value and condition expressions) the key
                     being inserted
=================== ==========================================================
