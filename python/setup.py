from setuptools import setup, find_packages

def main(setup_func=setup):
    install_requires = [
    ]

    test_requires = [
        'pytest',
        'pylint',
        'flake8'
    ]


    setup_func(
        version="0.0.2",
        name='dataservices',
        packages=find_packages(),
        install_requires=install_requires,
        test_require=test_requires,
        extras_require={
            'testing': test_requires,
        },
    )


main()
