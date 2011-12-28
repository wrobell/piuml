#!/usr/bin/env python3

import sys
import os.path

from setuptools import setup, find_packages

setup(
    name='piuml',
    version='0.1.0',
    description='piUML is piUML language parser and UML diagram generator',
    author='Artur Wroblewski',
    author_email='wrobell@pld-linux.org',
    url='http://wrobell.it-zone.org/piuml',
    package_dir={'': 'src'},
    packages=find_packages('.'),
    scripts=('bin/piuml',),
    include_package_data=True,
    long_description=\
"""\
piUML is piUML language parser and UML diagram generator.
""",
    classifiers=[
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Programming Language :: Python',
        'Development Status :: 1 - Alpha',
        'Topic :: Software Development',
    ],
    keywords='UML modeling programming documentation',
    license='GPL',
    install_requires=['arouter >= 0.1.0', 'distribute', 'setuptools-git'],
    test_suite='nose.collector',
)

# vim: sw=4:et:ai
