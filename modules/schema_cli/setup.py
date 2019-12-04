from setuptools import setup
from setuptools import find_packages

setup(
    name="schema_cli",
    version="0.0.1",
    description="Module to use schema code through cli",
    long_description="Module to use schema code through cli",
    author="Jan Murre",
    author_email="jan.murre@catalyz.nl",
    url="",
    packages=find_packages(),
    install_requires=[
        "click",
        "schema_ingest",
    ],
    extras_require={"tests": ["pytest"]},
    entry_points="""
        [console_scripts]
        schema=schema_cli:main
    """
)
