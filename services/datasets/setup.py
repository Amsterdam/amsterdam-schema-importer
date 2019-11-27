from setuptools import setup, find_packages

def main(setup_func=setup):
    install_requires = [
        'ndjson',
    ]

    test_requires = [
        'pytest',
        'pylint',
        'flake8'
    ]


    setup_func(
        version="0.0.1",
        name='datasets',
        packages=find_packages(include=('datasets', )),
        install_requires=install_requires,
        test_require=test_requires,
        extras_require={
            'testing': test_requires,
        },
        python_requires='>=3.6',
    )


main()
