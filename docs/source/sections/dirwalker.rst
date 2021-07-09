Directory Walker section
========================

An directory walker source section yields a hierarchy of items with
paths from a filesystem using `os.walk()`_.

    >>> infologger = """
    ... [transmogrifier]
    ... pipeline =
    ...     source
    ...     logger
    ...
    ... [source]
    ... blueprint = collective.transmogrifier.sections.dirwalker
    ... dirname = collective.transmogrifier:.
    ... sort-key = python:not basename.lower().startswith('dir'), basename
    ...
    ... [logger]
    ... blueprint = collective.transmogrifier.sections.logger
    ... name = logger
    ... level = INFO
    ... """
    >>> registerConfig('collective.transmogrifier.sections.tests.dirwalker',
    ...                infologger)
    >>> transmogrifier('collective.transmogrifier.sections.tests.dirwalker')
    >>> print(handler)
    logger INFO
      {'_path': '/', '_type': 'Folder'...
    logger INFO
      {'_path': '__init__.py'...
    logger INFO
      {'_path': 'sections/', '_type': 'Folder'...
    logger INFO
      {'_path': 'tests/', '_type': 'Folder'...
    logger INFO
      {'_path': 'sections/dirwalker.py'...
    logger INFO
      {'_path': 'sections/breakpoint.py'...
