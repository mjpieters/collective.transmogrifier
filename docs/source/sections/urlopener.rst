URL Opener section
==================

An URL opener source section requests a URL and inserts keys for the
response and header optionally also using a local cache.

    >>> urlopener = """
    ... [transmogrifier]
    ... pipeline =
    ...     source
    ...     url
    ...     urlopen
    ...     headers
    ...     logger
    ...
    ... [source]
    ... blueprint = collective.transmogrifier.sections.csvsource
    ... filename = collective.transmogrifier.tests:urlopener.csv
    ...
    ... [url]
    ... blueprint = collective.transmogrifier.sections.inserter
    ... key = string:_url
    ... condition = python:not modules['urllib.parse'].urlsplit(
    ...     item.get('_url', '')).netloc
    ... value = python:'file://' + modules['posixpath'].join(
    ...     modules['os.path'].dirname(
    ...         modules['collective.transmogrifier'].__file__), item['_url'])
    ...
    ... [urlopen]
    ... blueprint = collective.transmogrifier.sections.urlopener
    ... handlers = python:[modules[
    ...     'collective.transmogrifier.sections.tests'].HTTPHandler]
    ... ignore-error = python:error.code == 404
    ... cache-directory = var/tests.urlopener.cache.d
    ...
    ... [headers]
    ... blueprint = collective.transmogrifier.sections.inserter
    ... key = string:_headers
    ... condition = exists:item/_headers
    ... value = python:dict(item['_headers'])
    ...
    ... [logger]
    ... blueprint = collective.transmogrifier.sections.logger
    ... name = logger
    ... level = INFO
    ... """
    >>> registerConfig(
    ...     'collective.transmogrifier.sections.tests.urlopener', urlopener)

    >>> transmogrifier('collective.transmogrifier.sections.tests.urlopener')
    >>> print(handler)
    logger INFO
        {'_cache': 'var/tests.urlopener.cache.d/http/foo/bar/qux/non-existent.html',
       '_headers': {'status': '404 Not Found',
                    'url': 'http://foo/bar/qux/non-existent.html'},
       '_url': 'http://foo/bar/qux/non-existent.html'}
    logger INFO
        {'_cache': 'var/tests.urlopener.cache.d/http/foo/bar/qux/redirect.html',
       '_headers': {'redirect-status': '301 Permanent',
                    'status': '200 Ok',
                    'url': 'http://foo/bar/qux/location.html'},
       '_url': 'http://foo/bar/qux/redirect.html'}

The cache directory has had response bodies written as files and
headers as RFC822 messages.

    >>> import os
    >>> import pprint
    >>> pprint.pprint(sorted(list(
    ...     (x[0], sorted(x[1]), sorted(x[2]))
    ...     for x in os.walk('var/tests.urlopener.cache.d')
    ... ), key= lambda x: x[0]))
    [('var/tests.urlopener.cache.d', ['http'], []),
     ('var/tests.urlopener.cache.d/http', ['foo'], []),
     ('var/tests.urlopener.cache.d/http/foo', ['bar'], []),
     ('var/tests.urlopener.cache.d/http/foo/bar', ['qux'], []),
     ('var/tests.urlopener.cache.d/http/foo/bar/qux',
      [],
      ['non-existent.html',
       'non-existent.html...',
       'redirect.html',
       'redirect.html...'])]
