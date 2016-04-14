Installation
============

 * When you're reading this you have probably already run
   ``easy_install collective.transmogrifier``. Find out how to install setuptools
   (and EasyInstall) here:
   http://peak.telecommunity.com/DevCenter/EasyInstall

 * Create a file called ``collective.transmogrifier-configure.zcml`` in the
   ``/path/to/instance/etc/package-includes`` directory.  The file
   should only contain this::

   <include package="collective.transmogrifier" />


Alternatively, if you are using zc.buildout and the plone.recipe.zope2instance
recipe to manage your project, you can do this:

 * Add ``collective.transmogrifier`` to the list of eggs to install, e.g.::

    [buildout]
    ...
    eggs =
        ...
        collective.transmogrifier

 * Tell the plone.recipe.zope2instance recipe to install a ZCML slug::

    [instance]
    recipe = plone.recipe.zope2instance
    ...
    zcml =
        collective.transmogrifier

 * Re-run buildout, e.g. with::

    $ ./bin/buildout

You can skip the ZCML slug if you are going to explicitly include the package
from another package's configure.zcml file.
