version = '1.1'

import os
from setuptools import setup, find_packages

def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

long_description = ('\n'.join((
    read('README.txt'), ''
    'Detailed Documentation',
    '**********************', '',
    read('src', 'collective', 'transmogrifier', 'transmogrifier.txt'), '',
    read('src', 'collective', 'transmogrifier', 'genericsetup.txt'), '',

    'Default section blueprints',
    '**************************',
    read('src', 'collective', 'transmogrifier', 'sections', 'constructor.txt'), '',
    read('src', 'collective', 'transmogrifier', 'sections', 'folders.txt'), '',
    read('src', 'collective', 'transmogrifier', 'sections', 'codec.txt'), '',
    read('src', 'collective', 'transmogrifier', 'sections', 'inserter.txt'), '',
    read('src', 'collective', 'transmogrifier', 'sections', 'condition.txt'), '',
    read('src', 'collective', 'transmogrifier', 'sections', 'manipulator.txt'), '',
    read('src', 'collective', 'transmogrifier', 'sections', 'splitter.txt'), '',
    read('src', 'collective', 'transmogrifier', 'sections', 'savepoint.txt'), '',
    read('src', 'collective', 'transmogrifier', 'sections', 'csvsource.txt'), '',

    read('docs', 'HISTORY.txt'), '',

    'Download',
    '********', ''
)))
    
open('doc.txt', 'w').write(long_description)

name='collective.transmogrifier'
setup(
    name=name,
    version=version,
    description='A configurable pipeline, aimed at transforming content for '
                'import and export',
    long_description=long_description,
    # Get more strings from http://www.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
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
