"""Installer for the collective.transmogrifier package."""

from setuptools import find_packages
from setuptools import setup


long_description = "\n\n".join(
    [
        open("README.rst").read(),
        open("CONTRIBUTORS.rst").read(),
        open("CHANGES.rst").read(),
    ]
)


setup(
    name="collective.transmogrifier",
    version="3.0.0",
    description="A configurable pipeline, aimed at transforming content for import and export",
    long_description=long_description,
    # Get more from https://pypi.org/classifiers/
    classifiers=[
        "Development Status :: 6 - Mature",
        "Environment :: Web Environment",
        "Framework :: Plone :: 5.2",
        "Framework :: Plone :: 6.0",
        "Framework :: Plone :: Addon",
        "Framework :: Plone",
        "Framework :: Zope2",
        "Framework :: Zope3",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="content import filtering",
    author="Jarn",
    author_email="info@jarn.com",
    url="https://github.com/collective/collective.transmogrifier",
    project_urls={
        "PyPI": "https://pypi.python.org/pypi/collective.transmogrifier",
        "Source": "https://github.com/collective/collective.transmogrifier",
        "Tracker": "https://github.com/collective/collective.transmogrifier/issues",
    },
    license="GPL version 2",
    packages=find_packages("src", exclude=["ez_setup"]),
    namespace_packages=["collective"],
    package_dir={"": "src"},
    include_package_data=True,
    zip_safe=False,
    python_requires=">=3.7",
    install_requires=[
        "Products.CMFCore",
        "setuptools",
        "zope.schema",
    ],
    extras_require={
        "test": [
            "zest.releaser[recommended]",
            "zope.testrunner",
        ]
    },
    entry_points="""
    [z3c.autoinclude.plugin]
    target = plone
    [console_scripts]
    update_locale = collective.transmogrifier.locales.update:update_locale
    """,
)
