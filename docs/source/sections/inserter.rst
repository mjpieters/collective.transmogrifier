Inserter section
================

An inserter pipeline section lets you define a key and value to insert into
pipeline items. The inserter section blueprint name is
``collective.transmogrifier.sections.inserter``.

A inserter section takes a ``key`` and a ``value`` TALES expression. These
expressions are evaluated to generate the actual key-value pair that gets
inserted. You can also specify an optional ``condition`` option; if given, the
key only gets inserted when the condition, which is also a TALES is true.

Because the inserter ``value`` expression has access to the original item, it
could even be used to change existing item values. Just target an existing
key, pull out the original value in the value expression and return a modified
version.

    >>> inserter = """
    ... [transmogrifier]
    ... pipeline =
    ...     source
    ...     simple-insertion
    ...     expression-insertion
    ...     transform-id
    ...     logger
    ...
    ... [source]
    ... blueprint = collective.transmogrifier.sections.tests.rangesource
    ... size = 3
    ...
    ... [simple-insertion]
    ... blueprint = collective.transmogrifier.sections.inserter
    ... key = string:foo
    ... value = string:bar (inserted into "${item/id}" by the "$name" section)
    ...
    ... [expression-insertion]
    ... blueprint = collective.transmogrifier.sections.inserter
    ... key = python:'foo-%s' % item['id'][-2:]
    ... value = python:int(item['id'][-2:]) * 15
    ... condition = python:int(item['id'][-2:])
    ...
    ... [transform-id]
    ... blueprint = collective.transmogrifier.sections.inserter
    ... key = string:id
    ... value = string:foo-${item/id}
    ...
    ... [logger]
    ... blueprint = collective.transmogrifier.sections.logger
    ... name = logger
    ... level = INFO
    ... """
    >>> registerConfig('collective.transmogrifier.sections.tests.inserter',
    ...                inserter)
    >>> transmogrifier('collective.transmogrifier.sections.tests.inserter')
    >>> print(handler)
    logger INFO
        {'foo': 'bar (inserted into "item-00" by the "simple-insertion" section)',
        'id': 'foo-item-00'}
    logger INFO
        {'foo': 'bar (inserted into "item-01" by the "simple-insertion" section)',
        'foo-01': 15,
        'id': 'foo-item-01'}
    logger INFO
        {'foo': 'bar (inserted into "item-02" by the "simple-insertion" section)',
        'foo-02': 30,
        'id': 'foo-item-02'}

The ``key``, ``value`` and ``condition`` expressions have access to the
following:

=================== ==========================================================
 ``item``            the current pipeline item
 ``transmogrifier``  the transmogrifier
 ``name``            the name of the inserter section
 ``options``         the inserter options
 ``modules``         sys.modules
 ``key``             (only for the value and condition expressions) the key
                     being inserted
=================== ==========================================================
