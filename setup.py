#
# Copyright 2017 the original author or authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

# Always prefer setuptools over distutils
from os import path
from setuptools import setup, find_packages

# io.open is needed for projects that support Python 2.7
# It ensures open() defaults to text mode with universal newlines,
# and accepts an argument to specify the text encoding
# Python 3 only projects can skip this import
from io import open

package = 'pyvoltha'
setup_dir = path.dirname(path.abspath(__file__))
version_file = path.join(setup_dir, "VERSION")

# Get the long description from the README file
with open(path.join(setup_dir, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

with open(version_file) as version_file:
    version = version_file.read().strip()

requirements = open(path.join(setup_dir, "requirements.txt")).read().splitlines()
required = [line for line in requirements if not line.startswith("-")]
print ("Required is '{}'".format(required))

setup(
    name=package,
    version=version,
    description='VOLTHA Python support libraries',
    author='Chip Boling',
    author_email='chip@bcsw.net',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://wiki.opencord.org/display/CORD/VOLTHA',

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    packages=find_packages(exclude=['test']),
    install_requires=[required],
    include_package_data=True,
)
