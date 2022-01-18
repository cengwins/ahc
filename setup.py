from setuptools import setup, find_packages


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="adhoccomputing",
    version='1.2.1',
    author="Ertan Onur",
    author_email="eronur@metu.edu.tr",
    description="A small example package",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cengwins/ahc",
    project_urls={
        "Bug Tracker": "https://github.com/cengwins/ahc/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(),
    python_requires=">=3.8",
)