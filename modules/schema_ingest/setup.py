from setuptools import setup
from setuptools import find_packages

setup(
    name="schema_ingest",
    version="0.0.2",
    description="Module to ingest amsterdam schema",
    long_description="Module to ingest amsterdam schema",
    author="Jan Murre",
    author_email="jan.murre@catalyz.nl",
    url="",
    packages=find_packages(),
    install_requires=[
        "requests",
        "SQLAlchemy",
        "jsonschema",
        "dataservices>=0.0.3",
        "ndjson",
        "shapely",
        "schema_db",
    ],
    extras_require={"tests": ["pytest"]},
)
