Breakpoint section
==================

A breakpoint section will stop and enter pdb when a specific condition is
met. This is useful for debugging, as you can add a brekpoint section just
before a section that gets an error on a specific item.

The alternative is to add a conditional breakpoint in the section that fails,
but that can require findning the code in some egg somewhere, adding the
breakpoint and restarting the server. This speeds up the process.

    >>> breaker = """
    ... [transmogrifier]
    ... pipeline =
    ...     source
    ...     breaker
    ...     logger
    ...
    ... [source]
    ... blueprint = collective.transmogrifier.sections.tests.rangesource
    ... size = 3
    ...
    ... [breaker]
    ... blueprint = collective.transmogrifier.sections.breakpoint
    ... condition = python: item['id'] == 'item-01'
    ...
    ... [logger]
    ... blueprint = collective.transmogrifier.sections.logger
    ... name = logger
    ... level = INFO
    ... """
    >>> registerConfig('collective.transmogrifier.sections.tests.breaker',
    ...                breaker)

Since pdb requires input, for this test we replace stdin with something
giving some input (just a continue cammand).

    >>> oldstdin = make_stdin('c\n')
    >>> transmogrifier('collective.transmogrifier.sections.tests.breaker')
    > .../collective.transmogrifier/src/collective/transmogrifier/sections/logger.py(...)__iter__()
    -> ...
    (Pdb) c
    >>> print(handler)
    logger INFO
        {'id': 'item-00'}
    logger INFO
        {'id': 'item-01'}
    logger INFO
        {'id': 'item-02'}


And finally we reset the stdin:

    >>> reset_stdin(oldstdin)

