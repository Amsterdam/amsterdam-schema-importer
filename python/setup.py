from setuptools import setup

def main(setup_func=setup):
    install_requires = [
    ]

    test_requires = [
        'pytest',
        'pylint',
        'flake8'
    ]


    setup_func(
        name='dataservices',
        packages=['dataservices'],
        install_requires=install_requires,
        test_require=test_requires,
        extras_require={
            'testing': test_requires,
        },
    )


main()