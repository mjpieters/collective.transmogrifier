Savepoint section
=================

A savepoint pipeline section commits a savepoint every so often, which has a
side-effect of freeing up memory. The savepoint section blueprint name is
``collective.transmogrifier.sections.savepoint``.

A savepoint section takes an optional ``every`` option, which defaults to
1000; a savepoint is committed every ``every`` items passing through the pipe.
A savepoint section doesn't alter the items in any way:

    >>> savepoint = """
    ... [transmogrifier]
    ... pipeline =
    ...     source
    ...     savepoint
    ...     
    ... [source]
    ... blueprint = collective.transmogrifier.sections.tests.rangesource
    ... size = 10
    ... 
    ... [savepoint]
    ... blueprint = collective.transmogrifier.sections.savepoint
    ... every = 3
    ... """
    >>> registerConfig(u'collective.transmogrifier.sections.tests.savepoint',
    ...                savepoint)

    We'll show savepoints being committed by overriding transaction.savepoint:

    >>> import transaction
    >>> original_savepoint = transaction.savepoint
    >>> counter = [0]
    >>> def test_savepoint(counter=counter, *args, **kw):
    ...     counter[0] += 1
    >>> transaction.savepoint = test_savepoint
    >>> transmogrifier(u'collective.transmogrifier.sections.tests.savepoint')
    >>> transaction.savepoint = original_savepoint
    >>> counter[0]
    3
