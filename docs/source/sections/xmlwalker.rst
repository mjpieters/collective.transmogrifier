XML Walker section
==================

An XML walker source section yields a hierarchy of items by iterating
over an `lxml.etree`_ tree of XML elements that match an `XPath`_.
This can be used to build content structure based on the sitemap or
navigation of a HTML web site.

Options starting with ``element-`` may contain expressions whose value
will be inserted into the element items.  The expressions have access
to the following:

=================== ==========================================================
 ``element``         the current walked element
 ``item``            the current walked element item to be yielded
 ``source_item``     the original item containing the walked tree
 ``tree``            the original walked tree
 ``transmogrifier``  the transmogrifier
 ``name``            the name of the inserter section
 ``options``         the inserter options
 ``modules``         sys.modules
=================== ==========================================================

Start with an HTML file containing a heirarchical navbar.

    >>> import os
    >>> html_file = os.path.join(
    ...     os.path.dirname(__file__), 'xmlwalker.html')

    >>> infologger = """
    ... [transmogrifier]
    ... pipeline =
    ...     source
    ...     parse
    ...     walk
    ...     defaultpage
    ...     clean
    ...     logger
    ...
    ... [source]
    ... blueprint = collective.transmogrifier.sections.tests.rangesource
    ... size = 1
    ...
    ... [parse]
    ... blueprint = collective.transmogrifier.sections.inserter
    ... key = string:_trees
    ... value = python:modules['lxml.html'].parse('{}').xpath(\
    ...     "//*[contains(@class, 'navbar')]//ul[contains(@class, 'nav')]")
    ...
    ... [walk]
    ... blueprint = collective.transmogrifier.sections.xmlwalker
    ... element-keys =
    ...     _path
    ...     title
    ... element-_path = python:element.attrib.get(\
    ...     'href', element.attrib.get('src', ''))
    ... element-title = python:element.text_content().strip()\
    ...     or element.attrib.get('alt', '')
    ...
    ... [defaultpage]
    ... blueprint = collective.transmogrifier.sections.inserter
    ... key = string:_defaultpage
    ... condition = python:item.get('_parent', dict()).pop('_parent', True)\
    ...     and item.get('_defaultpage')
    ... value = exists:item/_defaultpage
    ...
    ... [clean]
    ... blueprint = collective.transmogrifier.sections.manipulator
    ... delete =
    ...     _trees
    ...     _element
    ...     id
    ...
    ... [logger]
    ... blueprint = collective.transmogrifier.sections.logger
    ... name = logger
    ... level = INFO
    ... """.format(html_file)
    >>> registerConfig(u'collective.transmogrifier.sections.tests.xmlwalker',
    ...                infologger)
    >>> transmogrifier(u'collective.transmogrifier.sections.tests.xmlwalker')
    >>> print(handler)
    logger INFO
      {}
    logger INFO
      {'_parent': {}, '_path': '#', '_type': 'Folder', 'title': 'Foo Tab'}
    logger INFO
        {'_is_defaultpage': True,
       '_parent': {'_path': '#', '_type': 'Folder', 'title': 'Foo Tab'},
       '_path': '#',
       'title': 'Foo Tab'}
    logger INFO
        {'_parent': {'_path': '#', '_type': 'Folder', 'title': 'Foo Tab'},
       '_path': '../foo-tab/index.html',
       'title': 'Foo Tab Default Page'}
    logger INFO
        {'_parent': {'_path': '#', '_type': 'Folder', 'title': 'Foo Tab'},
       '_path': '../foo-tab/bar-image.png',
       'title': 'Bar Image'}
    logger INFO
        {'_parent': {'_path': '#', '_type': 'Folder', 'title': 'Foo Tab'},
       '_path': '../foo-tab/qux-page.html',
       'title': 'Qux Page'}
    logger INFO
      {'_parent': {}, '_path': '#', '_type': 'Folder', 'title': 'Company'}
    logger INFO
        {'_is_defaultpage': True,
       '_parent': {'_path': '#', '_type': 'Folder', 'title': 'Company'},
       '_path': '#',
       'title': 'Company'}
    logger INFO
        {'_parent': {'_path': '#', '_type': 'Folder', 'title': 'Company'},
       '_path': '../company/news.html',
       '_type': 'Folder',
       'title': 'News'}
    logger INFO
        {'_is_defaultpage': True,
       '_parent': {'_path': '../company/news.html',
                   '_type': 'Folder',
                   'title': 'News'},
       '_path': '../company/news.html',
       'title': 'News'}
    logger INFO
        {'_parent': {'_path': '../company/news.html',
                   '_type': 'Folder',
                   'title': 'News'},
       '_path': '../company/news.html',
       'title': 'News'}
    logger INFO
        {'_parent': {'_path': '../company/news.html',
                   '_type': 'Folder',
                   'title': 'News'},
       '_path': '../company/press_releases.html',
       'title': 'Press Releases'}
    logger INFO
        {'_parent': {'_path': '#', '_type': 'Folder', 'title': 'Company'},
       '_path': '../company/events.html',
       'title': 'Events'}
    logger INFO
        {'_parent': {'_path': '#', '_type': 'Folder', 'title': 'Company'},
       '_path': '../contact_us/contact.html',
       'title': 'Contact Us'}
    logger INFO
        {'_parent': {'_path': '#', '_type': 'Folder', 'title': 'Company'},
       '_path': '../company/index.html',
       '_type': 'Folder',
       'title': 'About Company'}
    logger INFO
        {'_is_defaultpage': True,
       '_parent': {'_path': '../company/index.html',
                   '_type': 'Folder',
                   'title': 'About Company'},
       '_path': '../company/index.html',
       'title': 'About Company'}
    logger INFO
        {'_parent': {'_path': '../company/index.html',
                   '_type': 'Folder',
                   'title': 'About Company'},
       '_path': '../company/management.html',
       'title': 'Management'}
    logger INFO
        {'_parent': {'_path': '../company/index.html',
                   '_type': 'Folder',
                   'title': 'About Company'},
       '_path': '../company/investors.html',
       'title': 'Investors'}
    logger INFO
        {'_parent': {'_path': '../company/index.html',
                   '_type': 'Folder',
                   'title': 'About Company'},
       '_path': '../company/careers.html',
       'title': 'Careers'}
    logger INFO
        {'_parent': {'_path': '../company/index.html',
                   '_type': 'Folder',
                   'title': 'About Company'},
       '_path': '../company/company.html',
       'title': 'About Us'}
