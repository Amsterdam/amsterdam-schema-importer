from setuptools import setup
from setuptools import find_packages

setup(
    name="schema_ingest",
    version="0.0.1",
    description="Module to ingest amsterdam schema",
    long_description="Module to ingest amsterdam schema",
    author="Jan Murre",
    author_email="jan.murre@catalyz.nl",
    url="",
    packages=find_packages(),
    install_requires=[
        "SQLAlchemy",
        "dataservices>=0.0.3"
    ],
    extras_require={"tests": ["pytest"]},
    entry_points="""
        [console_scripts]
        schema_ingest=schema_ingest:main
    """
)
