# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
import os
import sys
import io
import re

with io.open('asyncaws/__init__.py', 'rt', encoding='utf8') as f:
    version = re.search(r'__version__ = \'(.*?)\'', f.read()).group(1)

setup(
    name="asyncaws",
    version=version,
    packages=find_packages(exclude=["tests.*", "tests"]),
    description="asyncio aws sdk",
    long_description="asyncio aws sdk",
    url='http://github.com/zeaphoo/asyncaws/',
    author="wei.zhuo",
    author_email="zeaphoo@qq.com",
    include_package_data=True,
    zip_safe=False,
    license="MIT",
    keywords=(),
    platforms="any",
    install_requires=['loguru'],
    entry_points={
    }
)
