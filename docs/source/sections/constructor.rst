Constructor section
===================

A constructor pipeline section is the heart of a transmogrifier content import
pipeline. It constructs Plone content based on the items it processes. The
constructor section blueprint name is
``collective.transmogrifier.sections.constructor``. Constructor sections do
only one thing, they construct *new* content. No schema changes are made.
Also, constructors create content without restrictions, no security checks or
containment constraints are checked.

Construction needs 2 pieces of information: the path to the item (including
the id for the new item itself) and it's portal type. To determine both of
these, the constructor section inspects each item and looks for 2 keys, as
described below. Any item missing any of these 2 pieces will be skipped.
Similarly, items with a path for a container or type that doesn't exist will
be skipped as well; make sure that these containers are constructed
beforehand. Because a constructor section will only construct new objects, if
an object with the same path already exists, the item will also be skipped.

For the object path, it'll look (in order) for
``_collective.transmogrifier.sections.constructor_[sectionname]_path``,
``_collective.transmogrifier.sections.constructor_path``,
``_[sectionname]_path``, and ``_path``, where ``[sectionname]`` is replaced
with the name given to the current section. This allows you to target the
right section precisely if needed. Alternatively, you can specify what key to
use for the path by specifying the ``path-key`` option, which should be a list
of keys to try (one key per line, use a ``re:`` or ``regexp:`` prefix to
specify regular expressions).

For the portal type, use the ``type-key`` option to specify a set of keys just
like ``path-key``. If omitted, the constructor will look for
``_collective.transmogrifier.sections.constructor_[sectionname]_type``,
``_collective.transmogrifier.sections.constructor_type``,
``_[sectionname]_type``, ``_type``, ``portal_type`` and ``Type`` (in that
order, with ``[sectionname]`` replaced).

Unicode paths will be encoded to ASCII. Using the path and type, a new object
will be constructed using invokeFactory; nothing else is done. Paths are
always interpreted as relative to the context object, with the last path
segment being the id of the object to create.

By default the constructor section will log a warning if the container for
the item is missing and the item can't be constructed. However if you add a
required = True key to the constructor section it will instead raise a KeyError.

    >>> import pprint
    >>> constructor = """
    ... [transmogrifier]
    ... pipeline =
    ...     contentsource
    ...     constructor
    ...     logger
    ...
    ... [contentsource]
    ... blueprint = collective.transmogrifier.sections.tests.contentsource
    ...
    ... [constructor]
    ... blueprint = collective.transmogrifier.sections.constructor
    ...
    ... [logger]
    ... blueprint = collective.transmogrifier.sections.logger
    ... name = logger
    ... level = INFO
    ... """
    >>> registerConfig('collective.transmogrifier.sections.tests.constructor',
    ...                constructor)
    >>> transmogrifier('collective.transmogrifier.sections.tests.constructor')
    >>> print(handler)
    logger INFO
      {'_path': '/eggs/foo', '_type': 'FooType'}
    logger INFO
      {'_path': '/spam/eggs/foo', '_type': 'FooType'}
    logger INFO
      {'_path': '/foo', '_type': 'FooType'}
    logger INFO
      {'_path': '/unicode/encoded/to/ascii', '_type': 'FooType'}
    logger INFO
        {'_path': 'not/existing/bar',
       '_type': 'BarType',
       'title': 'Should not be constructed, not an existing path'}
    logger INFO
        {'_path': '/spam/eggs/existing',
       '_type': 'FooType',
       'title': 'Should not be constructed, an existing object'}
    logger INFO
        {'_path': '/spam/eggs/incomplete',
       'title': 'Should not be constructed, no type'}
    logger INFO
        {'_path': '/spam/eggs/nosuchtype',
       '_type': 'NonExisting',
       'title': 'Should not be constructed, not an existing type'}
    logger INFO
        {'_path': 'spam/eggs/changedByFactory',
       '_type': 'FooType',
       'title': 'Factories are allowed to change the id'}
    >>> pprint.pprint(plone.constructed)
    [('eggs', 'foo', 'FooType'),
     ('spam/eggs', 'foo', 'FooType'),
     ('', 'foo', 'FooType'),
     ('unicode/encoded/to', 'ascii', 'FooType'),
     ('spam/eggs', 'changedByFactory', 'FooType')]

    >>> constructor = """
    ... [transmogrifier]
    ... pipeline =
    ...     contentsource
    ...     constructor
    ...     logger
    ...
    ... [contentsource]
    ... blueprint = collective.transmogrifier.sections.tests.contentsource
    ...
    ... [constructor]
    ... blueprint = collective.transmogrifier.sections.constructor
    ... required = True
    ...
    ... [logger]
    ... blueprint = collective.transmogrifier.sections.logger
    ... name = logger
    ... level = INFO
    ... """
    >>> registerConfig('collective.transmogrifier.sections.tests.constructor2',
    ...                constructor)
    >>> handler.clear()
    >>> try:
    ...     transmogrifier('collective.transmogrifier.sections.tests.constructor2')
    ...     raise AssertionError("Required constructor did not raise an error for missing folder")
    ... except KeyError:
    ...     pass
    >>> print(handler)
    logger INFO
      {'_path': '/eggs/foo', '_type': 'FooType'}
    logger INFO
      {'_path': '/spam/eggs/foo', '_type': 'FooType'}
    logger INFO
      {'_path': '/foo', '_type': 'FooType'}
    logger INFO
      {'_path': '/unicode/encoded/to/ascii', '_type': 'FooType'}
