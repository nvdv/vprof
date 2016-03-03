[![Build Status](https://travis-ci.org/nvdv/vprof.svg?branch=master)](https://travis-ci.org/nvdv/vprof)

# vprof

vprof is a Python package providing rich and interactive visualizations for
various Python program characteristics such as running time and memory usage.
It supports Python 2.7, Python 3.4, Python 3.5 and distributed under BSD license.

The project is in active development and some of it's features might not work as
expected.

## Screenshots

![flame-chart](http://i.imgur.com/mbszOET.png?1)
![memory-stats](http://i.imgur.com/jTJGu2t.png?1)
![code-heatmap](http://i.imgur.com/0FNdQHN.png?1)

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

    python setup.py install

To install just ```vprof``` dependencies, run

    python setup.py deps_install


## Usage

    vprof <modes> <test_script>

Supported modes:

* ```c``` - flame chart. Renders running time visualization for ```<test_script>```.
* ```m``` - memory graph. Shows memory usage during execution of each line of ```<test_script>```.
* ```h``` - code heatmap. Shows number of executions of each line of code.

Use double quotes to run scripts with arguments:

    vprof cmh "testscript.py --foo --bar"

Modes can be combined:

    vprof cm testscript.py

Check ```vprof -h``` for full list of supported parameters.

## Testing
Just run

    python setup.py test && python setup.py e2e_test

## License
BSD
