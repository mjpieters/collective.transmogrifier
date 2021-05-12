# -*- coding: utf-8 -*-

from Products.CMFPlone.utils import getFSVersionTuple


version_tuple = getFSVersionTuple()
PLONE_VERSION = '{0}{1}'.format(version_tuple[0], version_tuple[1])

BIGGER_THEN_PLONE51 = PLONE_VERSION > '51'
