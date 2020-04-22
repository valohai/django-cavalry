import re
import setuptools

with open('./cavalry/__init__.py', 'r') as infp:
    version = re.search("__version__ = ['\"]([^'\"]+)['\"]", infp.read()).group(1)

dev_dependencies = [
    'black',
    'flake8',
    'isort',
    'pydocstyle',
    'pytest-cov',
    'pytest-django>=3.7.0',
    'requests-mock',
]

if __name__ == '__main__':
    setuptools.setup(
        name='django-cavalry',
        description='Performance tracer middleware for Django',
        version=version,
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
        python_requires='>=3.6',
    )
