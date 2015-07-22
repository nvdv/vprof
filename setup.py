from setuptools import setup

setup(
    name='vprof',
    version='0.1',
    packages=['vprof'],
    description="Visual profiler for Python",
    url='http//github.com/nvdv/vprof',
    license='BSD',
    author='nvdv',
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'vprof = vprof.__main__:main'
        ]
    },
)