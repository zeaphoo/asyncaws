# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
import os
import sys
import io
import re

with io.open('clientmaker/__init__.py', 'rt', encoding='utf8') as f:
    version = re.search(r'__version__ = \'(.*?)\'', f.read()).group(1)

setup(
    name="clientmaker",
    version=version,
    packages=find_packages(exclude=["tests.*", "tests"]),
    description="service client auto generator",
    long_description="service client auto generator",
    url='http://github.com/zeaphoo/clientmaker/',
    author="wei.zhuo",
    author_email="zeaphoo@qq.com",
    include_package_data=True,
    zip_safe=False,
    license="MIT",
    keywords=(),
    platforms="any",
    install_requires=[],
    entry_points={
    }
)
