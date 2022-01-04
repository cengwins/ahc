import enum
from setuptools import setup


setup(
  # TODO: Fix the configs in this part
  name='ahc',
  version='0.1.0',    
  description='AHC: Wireless Ad Hoc Cloud Computing, Learning and Experimentation Environment',
  url='https://gitlab.ceng.metu.edu.tr/group-17/ahc-library',
  author='CengWins',
  author_email='eronur@metu.edu.tr',
  license='BSD 2-clause',
  packages=['ahc'],
  install_requires=[
    'matplotlib',
    'mnist',
    'networkx',
    'numpy',
    'pandas',
    'Pillow',
    'pygraphviz',
    'scikit_learn',
    'seaborn',
    'setuptools',
    'torch',

  ],
  classifiers=[],
)