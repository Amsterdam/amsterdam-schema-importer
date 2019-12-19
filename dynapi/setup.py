from setuptools import setup
from setuptools import find_packages

setup(
    name="dynapi",
    version="0.0.1",
    description="Dynamically generated REST API",
    long_description="Dynamically generated REST API",
    author="Jan Murre",
    author_email="jan.murre@catalyz.nl",
    url="",
    packages=find_packages(),
    install_requires=[
        "Flask-API",
        "Flask-SACore",
        "Flask-Cors",
        "psycopg2-binary",
        "SQLAlchemy",
        "sentry-sdk[flask]",
        "pint",
    ],
    extras_require={"tests": ["pytest"]},
)
