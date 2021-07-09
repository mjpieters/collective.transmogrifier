Logger section
================

First we need to set up a logger for testing:

    >>> import logging, sys
    >>> logger = logging.getLogger()
    >>> handler = logging.StreamHandler(sys.stdout)
    >>> handler.setFormatter(logging.Formatter('%(name)s: %(message)s'))
    >>> logger.addHandler(handler)

A logger section lets you log a piece of data from the item together with a
name. You can set any logging level in the logger. The logger blueprint name
is ``collective.transmogrifier.sections.logger``.

    >>> infologger = """
    ... [transmogrifier]
    ... pipeline =
    ...     source
    ...     logger
    ...
    ... [source]
    ... blueprint = collective.transmogrifier.sections.tests.rangesource
    ... size = 3
    ...
    ... [logger]
    ... blueprint = collective.transmogrifier.sections.logger
    ... level = INFO
    ... name = Infologger test
    ... key = id
    ... """
    >>> registerConfig('collective.transmogrifier.sections.tests.infologger',
    ...                infologger)
    >>> transmogrifier('collective.transmogrifier.sections.tests.infologger')
    Infologger test: item-00
    Infologger test: item-01
    Infologger test: item-02


We can also have numerical levels, and if the key is missing, it will print out
a message to that effect.  A condition may also be used to restrict
the items logged.

    >>> debuglogger = """
    ... [transmogrifier]
    ... pipeline =
    ...     source
    ...     logger
    ...
    ... [source]
    ... blueprint = collective.transmogrifier.sections.tests.rangesource
    ... size = 3
    ...
    ... [logger]
    ... blueprint = collective.transmogrifier.sections.logger
    ... level = 10
    ... name = Infologger test
    ... key = foo
    ... condition = python:item['id'] != 'item-01'
    ... """
    >>> registerConfig('collective.transmogrifier.sections.tests.debuglogger',
    ...                debuglogger)
    >>> transmogrifier('collective.transmogrifier.sections.tests.debuglogger')
    Infologger test: -- Missing key --
    Infologger test: -- Missing key --

If no ``key`` option is given, the logger will render the whole item
in a readable format using Python's ``pprint`` module.  The ``delete``
option can be used to omit certain keys from the output, such as body
text fields which may be too large and make the output too noisy.

    >>> logger = """
    ... [transmogrifier]
    ... pipeline =
    ...     source
    ...     logger
    ...
    ... [source]
    ... blueprint = collective.transmogrifier.sections.tests.samplesource
    ...
    ... [logger]
    ... blueprint = collective.transmogrifier.sections.logger
    ... level = INFO
    ... delete =
    ...     title-duplicate
    ...     id-duplicate
    ...     nonexistent
    ... """
    >>> registerConfig('collective.transmogrifier.sections.tests.logger',
    ...                logger)
    >>> transmogrifier('collective.transmogrifier.sections.tests.logger')
    collective.transmogrifier.sections.tests.logger.logger:
      {'id': 'foo', 'status': '℗', 'title': 'The Foo Fighters ℗'}
    collective.transmogrifier.sections.tests.logger.logger:
      {'id': 'bar', 'status': '™', 'title': 'Brand Chocolate Bar ™'}
    collective.transmogrifier.sections.tests.logger.logger:
      {'id': 'monty-python', 'status': '©', 'title': "Monty Python's Flying Circus ©"}
