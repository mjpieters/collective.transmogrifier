# -*- coding: utf-8 -*-
"""Installer for the collective.transmogrifier package."""

from setuptools import find_packages
from setuptools import setup


version = '1.5.3.dev0'
long_description = '\n\n'.join([
    open('README.rst').read(),
    open('CHANGES.rst').read(),
])

setup(
    name='collective.transmogrifier',
    version=version,
    description='A configurable pipeline, aimed at transforming content for '
                'import and export',
    long_description=long_description,
    classifiers=[
        'Framework :: Plone'
    ],
    keywords='content import filtering',
    author='Jarn',
    author_email='info@jarn.com',
    url='http://pypi.python.org/pypi/collective.transmogrifier',
    license='GPL',
    packages=find_packages('src', exclude=['ez_setup']),
    package_dir={'': 'src'},
    namespace_packages=['collective'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'setuptools',
        'Products.CMFCore',
    ],
)
