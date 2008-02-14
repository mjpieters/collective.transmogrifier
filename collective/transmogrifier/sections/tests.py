import unittest
from zope.testing import doctest
from collective.transmogrifier.tests import setUp, tearDown

def test_suite():
    return unittest.TestSuite((
        doctest.DocFileSuite(
            'splitter.txt',
            setUp=setUp, tearDown=tearDown),
    ))

    return suite
