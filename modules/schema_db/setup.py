from setuptools import setup
from setuptools import find_packages

setup(
    name="schema_db",
    version="0.0.3",
    description="Module to work with Postgres dbs",
    long_description="Module to work with Postgres dbs",
    author="Jan Murre",
    author_email="jan.murre@catalyz.nl",
    url="",
    packages=find_packages(),
    install_requires=["GeoAlchemy2", "dataservices>=0.0.3", "psycopg2"],
    extras_require={"tests": ["pytest"]},
)
