"""
===============================================================================
This file is part of GIAS2. (https://bitbucket.org/jangle/gias2)

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
===============================================================================
"""

#!/usr/bin/env python
from setuptools import setup, find_packages

import sys
from os import path
SELF_DIR = path.split(__file__)[0]
sys.path.append(path.join(SELF_DIR, 'src'))
from gias2.version import __version__

def readme():
     with open('README.md', 'r') as f:
          return f.read()

#=============================================================================#
name = 'gias2'
version = __version__
install_requires = [
     'numpy >= 1.6.1',
     'scipy >= 0.9',
     'scikit-learn >= 0.15',
     'scikit-image >= 0.13.0',
     # 'vtk',
     'cython >= 0.27.0',
     'matplotlib',
     'https://github.com/juzhang/pydicom/archive/sys-fix.zip'
]
if sys.version_info.major==2:
     install_requires.append('ConfigParser')
else:
     install_requires.append('configparser')

package_data = {
     'gias2': [
          'src/gias2/examples/data/*',
          'src/gias2/examples/outputs/*.md',
          'src/gias2/examples/data/tetgen_mesh/*',
          'src/gias2/examples/fieldwork/data/*',
          'src/gias2/examples/fieldwork/fit_whole_pelvis_data/*',
     ],
}
include_package_data = True
description = 'A library of musculoskeletal modelling tools.'
author = 'MAP Client Developers'
url = 'https://bitbucket.org/jangle/gias2'
keywords = 'musculoskeletal map mapclient'
license = 'mozilla'
classifiers = [
     'Development Status :: 3 - Alpha',
     'License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)',
     'Programming Language :: Python :: 2.7',
     'Programming Language :: Python :: 3.5',
     'Topic :: Scientific/Engineering :: Medical Science Apps.'
]
entry_points = {
     'console_scripts': [
          'gias-rbfreg=gias2.applications.giasrbfreg:main',
          'gias-rigidreg=gias2.applications.giasrigidreg:main',
          'gias-pcreg=gias2.applications.giaspcreg:main',
          'gias-trainpcashapemodel=gias2.applications.giastrainpcashapemodel:main',
          'gias-surfacedistance=gias2.applications.giassurfacedistance:main',
          'gias-hmfinp2surf=gias2.applications.giashmfinp2surf:main',
          'gias-inpsampledicom=gias2.applications.giasinpsampledicom:main'
     ]
}

#=============================================================================#
if __name__ == '__main__':
     setup(
          name=name,
          version=version,
          description=description,
          long_description=readme(),
          packages=find_packages(where="src"),
          package_data=package_data,
          include_package_data=include_package_data,
          package_dir={"": "src"},
          classifiers=classifiers,
          author=author,
          url=url,
          install_requires=install_requires,
          keywords=keywords,
          license=license,
          # scripts=scripts,
          entry_points = entry_points,
     )