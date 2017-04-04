import setuptools

dev_dependencies = [
    'flake8',
    'isort',
    'pydocstyle',
    'pytest-cov',
    'pytest-django>=3.0.0',
    'requests-mock',
]

if __name__ == '__main__':
    setuptools.setup(
        name='django-cavalry',
        description='Performance tracer middleware for Django',
        version='0.0.0',
        url='https://github.com/valohai/django-cavalry',
        author='Valohai',
        maintainer='Aarni Koskela',
        maintainer_email='akx@iki.fi',
        license='MIT',
        install_requires=['Django', 'requests'],
        tests_require=dev_dependencies,
        extras_require={'dev': dev_dependencies},
        packages=setuptools.find_packages('.', exclude=('cavalry_tests',)),
        include_package_data=True,
    )
