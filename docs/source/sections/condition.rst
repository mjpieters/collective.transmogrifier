Condition section
=================

A condition pipeline section lets you selectively discard items from the
pipeline. The condition section blueprint name is
``collective.transmogrifier.sections.condition``.

A condition section takes a ``condition`` TALES expression. When this
expression when matched against the current item is True, the item is yielded
to the next pipe section, otherwise it is not:

    >>> condition = """
    ... [transmogrifier]
    ... pipeline =
    ...     source
    ...     condition
    ...     logger
    ...
    ... [source]
    ... blueprint = collective.transmogrifier.sections.tests.rangesource
    ... size = 5
    ...
    ... [condition]
    ... blueprint = collective.transmogrifier.sections.condition
    ... condition = python:int(item['id'][-2:]) > 2
    ...
    ... [logger]
    ... blueprint = collective.transmogrifier.sections.logger
    ... name = logger
    ... level = INFO
    ... """
    >>> registerConfig('collective.transmogrifier.sections.tests.condition',
    ...                condition)
    >>> transmogrifier('collective.transmogrifier.sections.tests.condition')
    >>> print(handler)
    logger INFO
        {'id': 'item-03'}
    logger INFO
        {'id': 'item-04'}

The ``condition`` expression has access to the following:

=================== ==========================================================
 ``item``            the current pipeline item
 ``transmogrifier``  the transmogrifier
 ``name``            the name of the splitter section
 ``options``         the splitter options
 ``modules``         sys.modules
=================== ==========================================================

As condition sections skip items in the pipeline, they should not be used
inside a splitter section!
