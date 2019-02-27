from setuptools import setup, find_packages

from docupdater import VERSION

requirements = ['docker>=3.7.0',
                'apscheduler>=3.5.3',
                'requests>=2.21.0',
                'apprise>=0.5.2',
                'jinja2>=2.10',
                'click>=7.0']


def read(filename):
    with open(filename) as f:
        return f.read()


setup(
    name='docupdater',
    version=VERSION,
    maintainer='Any github maintainer',
    maintainer_email='harcher81@gmail.com',
    description='Automatically keep your docker services and your docker containers up-to-date with the latest version',
    long_description=read('README.md'),
    long_description_content_type='text/markdown',
    url='https://docupdater.github.io/docupdater/',
    license='MIT',
    classifiers=['Programming Language :: Python',
                 'Programming Language :: Python :: 3.6',
                 'Programming Language :: Python :: 3.7'],
    packages=find_packages(),
    include_package_data=True,
    scripts=['entrypoint'],
    install_requires=requirements,
    python_requires='>=3.6.2'
)
