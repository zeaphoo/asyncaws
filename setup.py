# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
import os
import sys
import io
import re

with io.open('asyncaws/__init__.py', 'rt', encoding='utf8') as f:
    version = re.search(r'__version__ = \'(.*?)\'', f.read()).group(1)

with open('README.md', 'rb') as f:
    long_description = f.read().decode('utf-8')


setup(
    name='asyncaws',
    version=version,
    url='https://github.com/zeaphoo/asyncaws/',
    license='MIT',
    author='Wei Zhuo',
    author_email='zeaphoo@qq.com',
    description='asyncio aws sdk.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=['asyncaws'],
    include_package_data=False,
    zip_safe=False,
    platforms='any',
    install_requires=['httpx'],
    extras_require={
        'dev': [
            'pytest>=3',
        ],
    },
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    python_requires='>=3.6',
    entry_points='''
    '''
)
