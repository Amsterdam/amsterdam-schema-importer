from setuptools import setup
from setuptools import find_packages

setup(
    name="shape_convert",
    version="0.0.2",
    description="Module to convert ESRI shape file to amsterdam schema + ndjson data",
    long_description="Module to convert ESRI shape file to amsterdam schema + ndjson data",
    author="Jan Murre",
    author_email="jan.murre@catalyz.nl",
    url="",
    packages=find_packages(),
    install_requires=[
        "requests",
        "jsonschema",
        "dataservices>=0.0.3",
        "ndjson",
        "shapely",
        "pyshp",
    ],
    extras_require={"tests": ["pytest"]},
)
