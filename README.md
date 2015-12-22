[![Build Status](https://travis-ci.org/nvdv/vprof.svg?branch=master)](https://travis-ci.org/nvdv/vprof)

# vprof

vprof is a Python package providing rich and interactive visualizations for
various Python program characteristics such as running time and memory usage.
The project is in active development and some of it's features might not work as
expected. It currently supports Python 2.7 and distributed under BSD license.

## Screenshots

![flame-chart](https://github.com/nvdv/vprof/raw/master/img/flame_chart.png)
![memory-stats](https://github.com/nvdv/vprof/raw/master/img/memory_stats.png)

## Dependencies
The required dependencies to build vprof are npm and Python 2. All Python
and npm module dependencies are listed in package.json, requirements.txt and
dev_requirements.txt.

## Installation
vprof can be installed from PyPI

    pip intall vprof

To install current dev version, clone this repository and execute

    make install

To install vprof dependencies:

    make deps_install

and

    make devdeps_install

## Usage
Currently vprof supports running time (via flame chart) and memory usage
visualization.
In order to get flame chart for specified Python program execute

    vprof c <test_script>

vprof will run test_script and open flame chart in new tab of default web
browser.

Memory stats visualization can be obtained by executing

    vprof m <test_script>

Options can be combined

    vprof cm <test_script>

Check ```vprof -h``` for full list of supported parameters.

## Testing
All tests can be run by executing

    make test


## License
BSD
