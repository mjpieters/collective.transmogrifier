# -*- coding: utf-8 -*-
"""Installer for the collective.transmogrifier package."""

from setuptools import find_packages
from setuptools import setup


long_description = '\n\n'.join([
    open('README.rst').read(),
    open('CONTRIBUTORS.rst').read(),
    open('CHANGES.rst').read(),
])


setup(
    name='collective.transmogrifier',
    version='1.5.3.dev0',
    description="A configurable pipeline, aimed at transforming content for import and export",
    long_description=long_description,
    # Get more from https://pypi.org/classifiers/
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Plone :: Addon",
        "Framework :: Plone :: 4.3",
        "Framework :: Plone :: 5.0",
        "Framework :: Plone :: 5.1",
        "Framework :: Plone :: 5.2",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
    ],
    keywords='content import filtering',
    author='Jarn',
    author_email='info@jarn.com',
    url='https://github.com/collective/collective.transmogrifier',
    project_urls={
        'PyPI': 'https://pypi.python.org/pypi/collective.transmogrifier',
        'Source': 'https://github.com/collective/collective.transmogrifier',
        'Tracker': 'https://github.com/collective/collective.transmogrifier/issues',
        # 'Documentation': 'https://collective.transmogrifier.readthedocs.io/en/latest/',
    },
    license='GPL version 2',
    packages=find_packages('src', exclude=['ez_setup']),
    namespace_packages=['collective'],
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    python_requires="==2.7, >=3.6",
    install_requires=[
        'Products.CMFCore',
        'setuptools',
        'six',
        'zope.schema',
    ],
    extras_require={
        'test': [
        ],
    },
    entry_points="""
    [z3c.autoinclude.plugin]
    target = plone
    [console_scripts]
    update_locale = collective.transmogrifier.locales.update:update_locale
    """,
)
