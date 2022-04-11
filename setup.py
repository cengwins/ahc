from setuptools import setup, find_packages


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()


setup(
  # TODO: Fix the configs in this part
  name='ahc',
  version='0.1.0',    
  description="Ad Hoc Computing Library",
  long_description=long_description,
  long_description_content_type="text/markdown",
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
    'yaml'
  ],
  project_urls={
        "Bug Tracker": "https://github.com/cengwins/ahc/issues",
  },
  classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
  python_requires=">=3.10",
)