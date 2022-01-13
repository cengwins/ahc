from setuptools import setup, find_packages

from ahc.Ahc import __version__


setup(
    name='ahc',
    version=__version__,

    url='https://github.com/cengwins/ahc',
    author='Ertan Onur',
    author_email='eronur@metu.edu.tr',

    #py_modules=['Ahc']
    packages=find_packages(),
)