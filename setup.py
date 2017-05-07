from setuptools import setup
import sys
import os

def read(fname):
  return open(os.path.join(os.path.dirname(__file__), fname)).read()

try:
  from PyQt4.QtCore import QT_VERSION_STR
except ImportError:
  sys.exit("PyQt4 is required to install this package (see README.md for installation instructions)")

setup(
  name = "wethepeopletoolkit",
  version = "1.0",
  author = "Alex Peattie",
  author_email = "me@alexpeattie.com",
  description = ("A project for analyzing and visualizing data from the Obama-era 'We the People' petitions site."),
  license = "MIT",
  keywords = "wethepeople petitions datascience analysis",
  url = "https://github.com/alexpeattie/wethepeopletoolkit",
  download_url = 'https://github.com/alexpeattie/wethepeopletoolkit/archive/1.0.tar.gz',
  install_requires=[
    'bs4',
    'click',
    'pandas',
    'numpy',
    'bitstring',
    'base58',
    'matplotlib',
    'findspark',
    'sklearn',
    'scipy'
  ],
  pymodules=['main'],
  entry_points='''
    [console_scripts]
    wethepeopletoolkit=main:cli
  ''',
  long_description=read('README.md'),
)