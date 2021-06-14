Codec section
=============

A codec pipeline section lets you alter the character encoding of item
values, allowing you to recode text from and to unicode and any of the
codecs supported by python. The codec section blueprint name is
``collective.transmogrifier.sections.codec``.

What values to recode is determined by the ``keys`` option, which takes a set
of newline-separated key names. If a key name starts with ``re:`` or
``regexp:`` it is treated as a regular expression instead.

The optional ``from`` and ``to`` options determine what codecs values are
recoded from and to. Both these values default to ``unicode``, meaning no
translation. If either option is set to ``default``, the current default
encoding of the Plone site is used.

To deal with possible encoding errors, you can set the error handler of both
the ``from`` and ``to`` codecs separately with the ``from-error-handler`` and
``to-error-handler`` options, respectively. These default to ``strict``, but
can be set to any error handler supported by python, including ``replace`` and
``ignore``.

Also optional is the ``condition`` option, which lets you specify a TALES
expression that when evaluating to False will prevent any en- or decoding from
happening. The condition is evaluated for every matched key.

    >>> codecs = """
    ... [transmogrifier]
    ... pipeline =
    ...     source
    ...     decode-all
    ...     encode-id
    ...     encode-title
    ...     logger
    ...
    ... [source]
    ... blueprint = collective.transmogrifier.sections.tests.samplesource
    ... encoding = utf8
    ...
    ... [decode-all]
    ... blueprint = collective.transmogrifier.sections.codec
    ... keys = re:.*
    ... from = utf8
    ...
    ... [encode-id]
    ... blueprint = collective.transmogrifier.sections.codec
    ... keys = id
    ... to = ascii
    ...
    ... [encode-title]
    ... blueprint = collective.transmogrifier.sections.codec
    ... keys = title
    ... to = ascii
    ... to-error-handler = backslashreplace
    ... condition = python:'Brand' not in item['title']
    ...
    ... [logger]
    ... blueprint = collective.transmogrifier.sections.logger
    ... name = logger
    ... level = INFO
    ... """
    >>> registerConfig('collective.transmogrifier.sections.tests.codecs',
    ...                codecs)
    >>> transmogrifier('collective.transmogrifier.sections.tests.codecs')
    >>> print(handler)
    logger INFO
      {'id': 'foo', 'status': '℗', 'title': 'The Foo Fighters \\u2117'}
    logger INFO
      {'id': 'bar', 'status': '™', 'title': 'Brand Chocolate Bar ™'}
    logger INFO
      {'id': 'monty-python', 'status': '©', 'title': "Monty Python's Flying Circus \\xa9"}

The ``condition`` expression has access to the following:

=================== ==========================================================
 ``item``            the current pipeline item
 ``key``             the name of the matched key
 ``match``           if the key was matched by a regular expression, the match
                     object, otherwise boolean True
 ``transmogrifier``  the transmogrifier
 ``name``            the name of the splitter section
 ``options``         the splitter options
 ``modules``         sys.modules
=================== ==========================================================
