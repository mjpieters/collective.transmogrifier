Folders section
===============

The ``collective.transmogrifier.sections.constructor`` blueprint can construct
new content, based on a type (``_type`` key) and a path (``_path`` key).
However, it will bail if it is asked to create an item for which the parent
folder does not exist.

One way to work around this is to ensure that the folders already exist, for
example by sending the instruction to construct them through the pipeline
before any contents of that folder. This requires sorted input, of course.

Alternatively, you can use the ``collective.transmogrifier.sections.folders``
blueprint. This will look at the path of each incoming item and construct
parent folders if needed. This implies that all folders (that do not yet
exist), are of the same type. That type defaults to ``Folder``, although you
can supply an alternative type. The folder will be created without an id only,
but a subsequent schema updated section for a subsequent item may have the
opportunity to update it (but not change its type.)

This blueprint can take the following options, all of the optional:

``path-key``
    The name of the key holding the path. This defaults to the same semantics
    as those used for the constructor section. Just use ``_path`` and you'll
    be OK.
``new-type-key``
    The type key to use when inserting a new item in the pipeline to create
    folders. The default is ``_type``. Change it if you need to target a
    specific constructor section.
``new-path-key``
    The path key to use when inserting a new item in the pipeline to create
    folders. The default is to use the same as the incoming path key. Change
    it if you need to target a specific constructor section.
``folder-type``
    The name of the portal type to use for new folders. Defaults to
    ``Folder``, which is the default folder type in CMF and Plone.
``cache``
    By default, the section will keep a cache in memory of each folder it has
    checked (and possibly created) to know whether it already exists. This
    saves a lot of traversal, especially if you have many items under a
    particular folder. This will use a small amount of memory. If you have
    millions of objects, you can trade memory for speed by setting this option
    to false.

Here is how it might look by default:

    >>> import pprint
    >>> constructor = """
    ... [transmogrifier]
    ... pipeline =
    ...     contentsource
    ...     folders
    ...     logger
    ...
    ... [contentsource]
    ... blueprint = collective.transmogrifier.sections.tests.folderssource
    ...
    ... [folders]
    ... blueprint = collective.transmogrifier.sections.folders
    ...
    ... [logger]
    ... blueprint = collective.transmogrifier.sections.logger
    ... name = logger
    ... level = INFO
    ... """
    >>> registerConfig('collective.transmogrifier.sections.tests.folders',
    ...                constructor)
    >>> transmogrifier('collective.transmogrifier.sections.tests.folders')
    >>> print(handler)
    logger INFO
        {'_path': '/foo', '_type': 'Document'}
    logger INFO
        {'_path': '/existing/foo', '_type': 'Document'}
    logger INFO
        {'_path': '/nonexisting', '_type': 'Folder'}
    logger INFO
        {'_path': '/nonexisting/alpha', '_type': 'Folder'}
    logger INFO
        {'_path': '/nonexisting/alpha/foo', '_type': 'Document'}
    logger INFO
        {'_path': '/nonexisting/beta', '_type': 'Folder'}
    logger INFO
        {'_path': '/nonexisting/beta/foo', '_type': 'Document'}
    logger INFO
        {'_type': 'Document'}
    logger INFO
        {'_folders_path': '/delta', '_type': 'Folder'}
    logger INFO
        {'_folders_path': '/delta/foo', '_type': 'Document'}

To specify alternate types and keys, we can do something like this:

    >>> import pprint
    >>> constructor = """
    ... [transmogrifier]
    ... pipeline =
    ...     contentsource
    ...     folders
    ...     logger
    ...
    ... [contentsource]
    ... blueprint = collective.transmogrifier.sections.tests.folderssource
    ...
    ... [folders]
    ... blueprint = collective.transmogrifier.sections.folders
    ... folder-type = My Folder
    ... new-type-key = '_folderconstructor_type
    ... new-path-key = '_folderconstructor_path
    ...
    ... [logger]
    ... blueprint = collective.transmogrifier.sections.logger
    ... name = logger
    ... level = INFO
    ... """
    >>> registerConfig('collective.transmogrifier.sections.tests.folders2',
    ...                constructor)
    >>> handler.clear()
    >>> plone.exists.clear()
    >>> transmogrifier('collective.transmogrifier.sections.tests.folders2')
    >>> print(handler)
    logger INFO
      {'_path': '/foo', '_type': 'Document'}
    logger INFO
      {'_path': '/existing/foo', '_type': 'Document'}
    logger INFO
        {"'_folderconstructor_path": '/nonexisting',
       "'_folderconstructor_type": 'My Folder'}
    logger INFO
        {"'_folderconstructor_path": '/nonexisting/alpha',
       "'_folderconstructor_type": 'My Folder'}
    logger INFO
        {'_path': '/nonexisting/alpha/foo', '_type': 'Document'}
    logger INFO
        {"'_folderconstructor_path": '/nonexisting/beta',
       "'_folderconstructor_type": 'My Folder'}
    logger INFO
        {'_path': '/nonexisting/beta/foo', '_type': 'Document'}
    logger INFO
        {'_type': 'Document'}
    logger INFO
        {"'_folderconstructor_path": '/delta',
        "'_folderconstructor_type": 'My Folder'}
    logger INFO
        {'_folders_path': '/delta/foo', '_type': 'Document'}
