"""Setup script for vprof."""
import glob
import pip
import shlex
import subprocess
import unittest

from distutils import cmd
from setuptools import setup
from setuptools.command.install import install
from pip.req import parse_requirements
from pip.download import PipSession


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
            'pylint --reports=n --rcfile=pylint.rc ' + ' '.join(
                glob.glob('vprof/*.py'))))
        subprocess.check_call(shlex.split(
            'pylint --reports=n --rcfile=pylint.rc ' + ' '.join(
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
            shlex.split('rm -rf vprof/frontend/vprof_min.js'))


class RunDepsInstallCommand(cmd.Command):
    description = 'Install dependencies'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        pip.main(['install', '-r', 'requirements.txt'])
        pip.main(['install', '-r', 'dev_requirements.txt'])
        subprocess.check_call(
            shlex.split('npm install'))


class VProfBuild(install):

    def run(self):
        subprocess.check_call(shlex.split('npm run build'))


class VProfInstall(install):

    def run(self):
        install.run(self)


setup(
    name='vprof',
    version='0.3',
    packages=['vprof'],
    description="Visual profiler for Python",
    url='http://github.com/nvdv/vprof',
    license='BSD',
    author='nvdv',
    author_email='modestdev@gmail.com',
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
    install_requires=[
        str(req.req) for req in parse_requirements('requirements.txt',
                                                   session=PipSession())
    ],
    cmdclass={
        'test': RunUnittestsCommand,
        'e2e_test': RunEndToEndTestCommand,
        'lint': RunLintCommand,
        'deps_install': RunDepsInstallCommand,
        'build_ui': VProfBuild,
        'install': VProfInstall,
    },
)
