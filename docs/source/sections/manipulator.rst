Manipulator section
===================

A manipulator pipeline section lets you copy, move or discard keys from the
pipeline. The manipulator section blueprint name is
``collective.transmogrifier.sections.manipulator``.

A manipulator section will copy keys when you specify a set of keys to copy,
and an expression to determine what to copy these to. These are the ``keys``
and ``destination`` options.

The ``keys`` option is a set of key names, one on each line; keynames starting
with ``re:`` or ``regexp:`` are treated as regular expresions. The
``destination`` expression is a TALES expression that can access not only the
item, but also the matched key and, if a regular expression was used, the
match object.

If a ``delete`` option is specified, it is also interpreted as a set of keys,
like the ``keys`` option. These keys will be deleted from the item; if used
together with the ``keys`` and ``destination`` options, keys will be renamed
instead of copied.

Also optional is the ``condition`` option, which lets you specify a TALES
expression that when evaluating to False will prevent any manipulation from
happening. The condition is evaluated for every matched key.

    >>> manipulator = """
    ... [transmogrifier]
    ... pipeline =
    ...     source
    ...     copy
    ...     rename
    ...     delete
    ...     logger
    ...
    ... [source]
    ... blueprint = collective.transmogrifier.sections.tests.samplesource
    ...
    ... [copy]
    ... blueprint = collective.transmogrifier.sections.manipulator
    ... keys =
    ...     title
    ...     id
    ... destination = string:$key-copy
    ...
    ... [rename]
    ... blueprint = collective.transmogrifier.sections.manipulator
    ... keys = re:([^-]+)-copy$
    ... destination = python:'%s-duplicate' % match.group(1)
    ... delete = ${rename:keys}
    ...
    ... [delete]
    ... blueprint = collective.transmogrifier.sections.manipulator
    ... delete = status
    ...
    ... [logger]
    ... blueprint = collective.transmogrifier.sections.logger
    ... name = logger
    ... level = INFO
    ... """
    >>> registerConfig('collective.transmogrifier.sections.tests.manipulator',
    ...                manipulator)
    >>> transmogrifier('collective.transmogrifier.sections.tests.manipulator')
    >>> print(handler)
    logger INFO
        {'id': 'foo',
        'id-duplicate': 'foo',
        'title': 'The Foo Fighters ℗',
        'title-duplicate': 'The Foo Fighters ℗'}
    logger INFO
        {'id': 'bar',
        'id-duplicate': 'bar',
        'title': 'Brand Chocolate Bar ™',
        'title-duplicate': 'Brand Chocolate Bar ™'}
    logger INFO
        {'id': 'monty-python',
        'id-duplicate': 'monty-python',
        'title': "Monty Python's Flying Circus ©",
        'title-duplicate': "Monty Python's Flying Circus ©"}
    >>> handler.clear()

The ``destination`` expression has access to the following:

=================== ==========================================================
 ``item``            the current pipeline item
 ``key``             the name of the matched key
 ``match``           if the key was matched by a regular expression, the match
                     object, otherwise boolean True
 ``transmogrifier``  the transmogrifier
 ``name``            the name of the splitter section
 ``options``         the splitter options
 ``modules``         sys.modules
=================== ==========================================================
