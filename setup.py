from setuptools import setup

setup(
    name='vprof',
    version='0.10.0',
    packages=['vprof'],
    description="Visual profiler for Python",
    url='http://github.com/nvdv/vprof',
    license='BSD',
    author='nvdv',
    include_package_data=True,
    keywords = ['debugging', 'profiling'],
    entry_points = {
        'console_scripts': [
            'vprof = vprof.__main__:main'
        ]
    },
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development',
    ],
)
