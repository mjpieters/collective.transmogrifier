===============================
collective.blueprint.listsource
===============================

The collective.blueprint.listsource transmogrifier blueprint can be
used to add recursion or looping to a pipeline.  Specifically,
sections down stream from the list source section can access the list
source section and inject items.

If items from sources before the listsource section are appended, then
a loop is formed.  If items from sources after the listsource section
are appended, then a form of recursion is added to the pipeline.  If
the ``keys`` or ``copy-keys`` options are used, then certain item keys
may be postponed while other items complete such as to defer
processing keys until other items are constructed.

Items from previous sections are yielded first until items are
appended to the listsource.  Then the listsource items are yielded
until the listsource is empty at which point it continues yielding
from previous sections.  This is to avoid keeping item references in
the listsource as much as possible, but care should still be taken not
to fill the list with too many items and that those items do not
contain memory or other resource intensive references.

Assemble and register a transmogrifier with a list source section.

    >>> lister = """
    ... [transmogrifier]
    ... pipeline =
    ...     source
    ...     list
    ...     logger
    ...     insert
    ...     append
    ...
    ... [source]
    ... blueprint = collective.transmogrifier.sections.tests.rangesource
    ... size = 1
    ...
    ... [list]
    ... blueprint = collective.transmogrifier.sections.listsource
    ...
    ... [logger]
    ... blueprint = collective.transmogrifier.sections.logger
    ... name = logger
    ... level = INFO
    ...
    ... [insert]
    ... blueprint = collective.transmogrifier.sections.inserter
    ... key = string:id
    ... value = python:'item-%02d' % (int(item['id'].rsplit('-', 1)[-1]) + 1)
    ...
    ... [append]
    ... blueprint = collective.transmogrifier.sections.listappender
    ... condition = python:item['id'] < 'item-03'
    ... section = list
    ... """
    >>> registerConfig(
    ...     'collective.transmogrifier.sections.tests.listsource',
    ...     lister)

Run the transmogrifier.  An item with contents corresponding the
section config is injected.  All values are stripped of whitespace.  A
variable whose name is listed in the listsource-lists variable will
be broken up on newlines into a list.

    >>> transmogrifier(
    ...     'collective.transmogrifier.sections.tests.listsource')
    >>> print(handler)
    logger INFO
        {'id': 'item-00'}
    logger INFO
        {'id': 'item-01'}
    logger INFO
        {'id': 'item-02'}
    >>> handler.clear()

Instead of diverting the whole item, the appender section can move or
copy keys from the original item into a new item which will be
appended to the list source.

    >>> lister = """
    ... [transmogrifier]
    ... include = collective.transmogrifier.sections.tests.listsource
    ... pipeline -=
    ...     logger
    ...     append
    ... pipeline +=
    ...     copy
    ...     append
    ...     logger
    ...
    ... [source]
    ... size = 3
    ...
    ... [copy]
    ... blueprint = collective.transmogrifier.sections.manipulator
    ... keys = id
    ... destination = string:copy
    ...
    ... [append]
    ... keys = python:['id']
    ... copy-keys = python:['copy']
    ... """
    >>> registerConfig(
    ...     'collective.transmogrifier.sections.tests.listsource-move',
    ...     lister)
    >>> transmogrifier(
    ...     'collective.transmogrifier.sections.tests.listsource-move')
    >>> print(handler)
    logger INFO
      {'copy': 'item-01'}
    logger INFO
      {'copy': 'item-02'}
    logger INFO
      {'copy': 'item-03', 'id': 'item-03'}
    logger INFO
      {'copy': 'item-02'}
    logger INFO
      {'copy': 'item-03', 'id': 'item-03'}
    logger INFO
      {'copy': 'item-03', 'id': 'item-03'}



The ``condition`` expression has access to the following:

=================== ==========================================================
 ``item``            the current pipeline item
 ``transmogrifier``  the transmogrifier
 ``name``            the name of the splitter section
 ``options``         the splitter options
 ``modules``         sys.modules
=================== ==========================================================




