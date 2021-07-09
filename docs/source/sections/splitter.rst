Splitter section
================

A splitter pipeline section lets you branch a pipeline into 2 or more
sub-pipelines. The splitter section blueprint name is
``collective.transmogrifier.sections.splitter``.

A splitter section takes 2 or more pipeline definitions, and sends the items
from the previous section through each of these sub-pipelines, each with it's
own copy [*]_ of the items:

    >>> emptysplitter = """
    ... [transmogrifier]
    ... pipeline =
    ...     source
    ...     splitter
    ...     logger
    ...
    ... [source]
    ... blueprint = collective.transmogrifier.sections.tests.rangesource
    ... size = 3
    ...
    ... [splitter]
    ... blueprint = collective.transmogrifier.sections.splitter
    ... pipeline-1 =
    ... pipeline-2 =
    ...
    ... [logger]
    ... blueprint = collective.transmogrifier.sections.logger
    ... name = logger
    ... level = INFO
    ... """
    >>> registerConfig('collective.transmogrifier.sections.tests.emptysplitter',
    ...                emptysplitter)
    >>> transmogrifier('collective.transmogrifier.sections.tests.emptysplitter')
    >>> print(handler)
    logger INFO
        {'id': 'item-00'}
    logger INFO
        {'id': 'item-00'}
    logger INFO
        {'id': 'item-01'}
    logger INFO
        {'id': 'item-01'}
    logger INFO
        {'id': 'item-02'}
    logger INFO
        {'id': 'item-02'}

Although the pipeline definitions in the splitter are empty, we end up with 2
copies of every item in the pipeline as both splitter pipelines get to process
a copy. Splitter pipelines are defined by options starting with ``pipeline-``.

Normally you'll use conditions to identify items for each sub-pipe, making the
splitter the pipeline equivalent of an if/elif statement. Conditions are
optional and use the pipeline option name plus ``-condition``:

    >>> evenoddsplitter = """
    ... [transmogrifier]
    ... pipeline =
    ...     source
    ...     splitter
    ...     logger
    ...
    ... [source]
    ... blueprint = collective.transmogrifier.sections.tests.rangesource
    ... size = 3
    ...
    ... [splitter]
    ... blueprint = collective.transmogrifier.sections.splitter
    ... pipeline-even-condition = python:int(item['id'][-2:]) % 2
    ... pipeline-even = even-section
    ... pipeline-odd-condition = not:${splitter:pipeline-even-condition}
    ... pipeline-odd = odd-section
    ...
    ... [odd-section]
    ... blueprint = collective.transmogrifier.sections.inserter
    ... key = string:even
    ... value = string:The even pipe
    ...
    ... [even-section]
    ... blueprint = collective.transmogrifier.sections.inserter
    ... key = string:odd
    ... value = string:The odd pipe
    ...
    ... [logger]
    ... blueprint = collective.transmogrifier.sections.logger
    ... name = logger
    ... level = INFO
    ... """
    >>> registerConfig('collective.transmogrifier.sections.tests.evenodd',
    ...                evenoddsplitter)
    >>> handler.clear()
    >>> transmogrifier('collective.transmogrifier.sections.tests.evenodd')
    >>> print(handler)
    logger INFO
        {'even': 'The even pipe', 'id': 'item-00'}
    logger INFO
        {'id': 'item-01', 'odd': 'The odd pipe'}
    logger INFO
        {'even': 'The even pipe', 'id': 'item-02'}

Conditions are expressed as TALES statements, and have access to:

=================== ==========================================================
 ``item``            the current pipeline item
 ``transmogrifier``  the transmogrifier
 ``name``            the name of the splitter section
 ``pipeline``        the name of the splitter pipeline this condition belongs
                     to (including the ``pipeline-`` prefix)
 ``options``         the splitter options
 ``modules``         sys.modules
=================== ==========================================================


.. WARNING::
    Although the splitter section employs some techniques to avoid memory
    bloat, if any contained section swallows items (so taking them from the
    previous section without passing them on), runs the risk of pulling all
    remaining items into the splitter buffer as a next match for the contained
    pipeline is being sought.

    You can avoid this by not using sections that discard items within a
    splitter; place these before or after a splitter section. Better still,
    use a correct condition in the splitter configuration that won't include
    the items to discard in the first place.

.. [*] Note that copy.deepcopy is used on all items. This will fail on items
    containing file handles, modules or other non-copyable values. See the
    copy module documentation.
