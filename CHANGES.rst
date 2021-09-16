Change History
**************

(name of developer listed in brackets)

2.0.0 (2021-09-16)
==================

- Add Python 3 e Plone 5.2 support.
  [wesleybl, zopyx, cdw9, rpatterson, flipmcf]

- Avoid failures if the ``id`` of an item is invalid for Zope.
  [hvelarde]


1.5.2 (2018-02-27)
==================

- pep 8, utf-8 headers, whitespace strip and sorted imports.
  [thet]

- Ignore - but log - rare cases of construction errors. Usually this
  happens for objects you do not want to migrate, but a detailed log entry is
  written.
  [sunew]


1.5.1 (2015-11-26)
==================

- Fix broken distribution.
  [hvelarde]


1.5 (2015-10-22)
================

- Allow csvsource to read files from GS import context
  [lentinj]

- Don't use traversal to avoid problems with acquisition or views.
  [rpatterson]

- Add csvsource support for taking the filename from an item key.
  [rpatterson]

- Add csvsource restkey handling for rows with more keys than fieldnames.
  [rpatterson]

- Add a blueprint for opening and caching URLs with ``urllib2``.
  [rpatterson]

- Add a source for walking a directory with ``os.walk``.
  [rpatterson]

- Add support for arbitrary csvsource fmtparam options.
  [rpatterson]

- Add DEBUG logging for expressions, useful for tracking changes to
  items as they move through the pipeline.
  [rpatterson]

- Add an XML walker source section for walking a tree of elements.
  [rpatterson]

- Add a list source section for adding recursion and/or looping to pipelines.
  [rpatterson]

- Add pprint support to the logger section, moved from the pprint
  section used in tests to make it more useful and available in actual
  pipelines.
  [rpatterson]

1.4 (2013-04-07)
================

- Fix the import location of the pagetemplate engine for newer Zope versions.
  [leorochael]

- Bug fix to load ZCML for GS when Products.GenericSetup is installed.
  [aclark]

1.3 (2011-03-17)
================

- Added the GenericSetup import context as an annotation to the transmogrifier.
  [elro]

- Added a logger to log the value of a particular key for all items. Handy
  when debugging, you can see which path is failing, and good if you want
  to show progress in a long import.
  [regebro]

- Added a breakpoint section to break on a particular expression, which is
  handy for debugging.
  [regebro]

1.2 (2010-03-30)
================

- Bug fix: the constructor promises to encode paths to ASCII, but failed to
  do so. Thanks to gyst for finding the discrepancy.
  [mj]

1.1 (2010-03-17)
================

- Allow the CSV source to load its file from a package as well as from an
  absolute or relative file path. To load from a package, pass
  ``package.name:filename.csv`` to the ``filename`` option.
  [optilude]

- Add CMF 2.2/Plone 4 compatibility for the content constructor
  [optilude]

- Use an explicit provides attribute to register the transmogrifier adapter.
  Fixes the "Missing 'provides' attribute" errors when loading with
  zope.annotation installed.
  [mj]

- Add a required flag to the content constructor, which causes it to raise
  a KeyError if the container where to construct the new item doesn't exist.
  [regebro]

- Add an optional condition to the manipulator section.
  [regebro]

1.0 (2009-08-07)
================

- Initial transmogrifier architecture.
  [mj]
