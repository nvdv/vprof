"""Setup script for vprof."""
import glob
import pip
import re
import shlex
import subprocess
import unittest

import pkg_resources
from distutils import cmd
from setuptools import setup
from setuptools.command.install import install


class RunUnittestsCommand(cmd.Command):
    description = 'Run all unittests'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        suite = unittest.TestLoader().discover(
            'vprof/tests/.', pattern="*_test.py")
        unittest.TextTestRunner(verbosity=2, buffer=True).run(suite)
        subprocess.check_call(shlex.split('npm run test'))


class RunEndToEndTestCommand(cmd.Command):
    description = 'Run all end to end tests'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        suite = unittest.TestLoader().discover(
            'vprof/tests/.', pattern="*_e2e.py")
        unittest.TextTestRunner(verbosity=2, buffer=True).run(suite)


class RunLintCommand(cmd.Command):
    description = 'Run linter'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        subprocess.check_call(shlex.split('npm run lint'))
        subprocess.check_call(shlex.split(
            'pylint --reports=n --rcfile=.pylintrc ' + ' '.join(
                glob.glob('vprof/*.py'))))
        subprocess.check_call(shlex.split(
            'pylint --reports=n --rcfile=.pylintrc ' + ' '.join(
                glob.glob('vprof/tests/*.py'))))


class RunCleanCommand(cmd.Command):
    description = 'Clean temporary files'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        subprocess.check_output(
            shlex.split('rm -rf vprof/ui/vprof_min.js'))


class RunDepsInstallCommand(cmd.Command):
    description = 'Install dependencies'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        subprocess.check_call(["python", '-m', 'pip', 'install', '-r', 'requirements.txt'])
        subprocess.check_call(["python", '-m', 'pip', 'install', '-r', 'dev_requirements.txt'])
        subprocess.check_call(shlex.split('npm install'))


class VProfBuild(install):

    def run(self):
        subprocess.check_call(shlex.split('npm run build'))


class VProfInstall(install):

    def run(self):
        install.run(self)


def get_vprof_version(filename):
    """Returns actual version specified in filename."""
    with open(filename) as src_file:
        version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                                  src_file.read(), re.M)
        if version_match:
            return version_match.group(1)
        raise RuntimeError('Unable to find version info.')


def get_description():
    """Reads README.md file."""
    with open('README.md') as readme_file:
        return readme_file.read()


def get_requirements():
    with open('requirements.txt') as fp:
        return [str(r) for r in pkg_resources.parse_requirements(fp)]


setup(
    name='vprof',
    version=get_vprof_version('vprof/__main__.py'),
    packages=['vprof'],
    description="Visual profiler for Python",
    url='http://github.com/nvdv/vprof',
    license='BSD',
    author='nvdv',
    author_email='aflatnine@gmail.com',
    include_package_data=True,
    keywords=['debugging', 'profiling'],
    entry_points={
        'console_scripts': [
            'vprof = vprof.__main__:main'
        ]
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development',
    ],
    install_requires=get_requirements(),
    long_description=get_description(),
    long_description_content_type="text/markdown",
    cmdclass={
        'test': RunUnittestsCommand,
        'e2e_test': RunEndToEndTestCommand,
        'lint': RunLintCommand,
        'deps_install': RunDepsInstallCommand,
        'build_ui': VProfBuild,
        'install': VProfInstall,
    },
)
