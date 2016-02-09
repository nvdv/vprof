[![Build Status](https://travis-ci.org/nvdv/vprof.svg?branch=master)](https://travis-ci.org/nvdv/vprof)

# vprof

vprof is a Python package providing rich and interactive visualizations for
various Python program characteristics such as running time and memory usage.
It supports Python 2.7, Python 3.x and distributed under BSD license.

The project is in active development and some of it's features might not work as
expected.

## Screenshots

![flame-chart](http://i.imgur.com/mbszOETh.png?1)
![memory-stats](http://i.imgur.com/jTJGu2th.png?1)
![code-heatmap](http://i.imgur.com/0FNdQHNh.png?1)

## Prerequisites
The required dependencies to build ```vprof``` from source code:
 * Python 2.7, Python 3.4 or Python 3.5
 * ```pip```
 * ```npm``` >= 3.3.12

## Dependencies
All Python and ```npm``` module dependencies are listed in package.json and requirements.txt.

## Installation
```vprof``` can be installed from PyPI

    pip install vprof

To install current dev version, clone this repository and execute

    make install

To install just ```vprof``` dependencies run

    make deps_install


## Usage
Currently ```vprof``` supports running time, memory usage and code heatmap
visualization.
In order to get running time visualization for specified Python program, run

    vprof c <test_script>

```vprof``` will run <test_script> and open flame chart in new tab of default web
browser.

Memory stats visualization can be obtained by executing

    vprof m <test_script>

Resulting graph will show memory usage during execution of each line of
Python program.

To get code heatmap for Python script execute

    vprof h <test_script>

Code heatmap will show number of executions of each line of code of ```<test_script>```.

Options can be combined

    vprof cm <test_script>

Check ```vprof -h``` for full list of supported parameters.

## Testing
To run test suite enter

    make test

## License
BSD
