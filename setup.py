#!/usr/bin/env python

# setup.py
# Install script for pyTensible
# Copyright (c) 2012 Morgan Borman
# E-mail: morgan.borman@gmail.com

# This software is licensed under the terms of the Zlib license.
# http://en.wikipedia.org/wiki/Zlib_License

from distutils.core import setup
from pyTensible import __version__ as VERSION

NAME = "pyTensible"

PACKAGES = ['pyTensible', 'pyTensible.base', 'pyTensible.base.pyTensible']
				
PACKAGE_DATA = {'pyTensible.base.pyTensible': ['manifest.mf']}

DESCRIPTION = 'A simple lightweight extension framework'

URL = 'http://cxsbs.org/pyTensible/'

DOWNLOAD_URL = "https://github.com/MorganBorman/pyTensible/downloads"

AUTHOR = 'Morgan Borman'

AUTHOR_EMAIL = 'morgan.borman@gmail.com'

CLASSIFIERS = [
    'Development Status :: 4 - Beta',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: zlib/libpng License',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2.7',
    'Operating System :: OS Independent',
    'Topic :: Software Development :: Libraries',
    'Topic :: Software Development :: Libraries :: Python Modules',
    'Natural Language :: English'
]

setup(name=NAME,
      version=VERSION,
      description=DESCRIPTION,
      author=AUTHOR,
      author_email=AUTHOR_EMAIL,
      url=URL,
      download_url=DOWNLOAD_URL,
      packages=PACKAGES,
      package_data=PACKAGE_DATA,
      classifiers=CLASSIFIERS
     )