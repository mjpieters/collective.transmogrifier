GenericSetup import integration
===============================

To ease running a transmogrifier pipeline during site configuration, a generic
import step for GenericSetup is included. 

The import step looks for a file named ``transmogrifier.txt`` and reads
pipeline configuration names from this file, one name per line. Empty lines
and lines starting with a # (hash mark) are skipped. These pipelines are then
executed in the same order as they are found in the file.

This means that if you want to run one or more pipelines as part of a
GenericSetup profile, all you have to do is name these pipelines in a file
named ``transmogrifier.txt`` in your profile directory.

The GenericSetup import context is stored on the transmogrifier as an
annotation::

    from collective.transmogrifier.genericsetup import IMPORT_CONTEXT
    from zope.annotation.interfaces import IAnnotations

    def __init__(self, transmogrifier, name, options, previous):
        self.import_context = IAnnotations(transmogrifier)[IMPORT_CONTEXT]

This will of course prevent your code from running outside the generic setup
import context.
