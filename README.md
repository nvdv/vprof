[![Build Status](https://travis-ci.org/nvdv/vprof.svg?branch=master)](https://travis-ci.org/nvdv/vprof)
[![PyPI](https://img.shields.io/pypi/v/vprof.svg)](https://pypi.python.org/pypi/vprof/)

# vprof

vprof is a Python package providing rich and interactive visualizations for
various Python program characteristics such as running time and memory usage.
It supports Python 2.7, Python 3.4, Python 3.5 and distributed under BSD license.

The project is in active development and some of its features might not work as
expected.

## Screenshots
![flame-graph](http://i.imgur.com/pwgmnho.png?1)
![memory-stats](http://i.imgur.com/lMS9qGz.png?1)
![code-heatmap](http://i.imgur.com/rWFqUfO.png?1)

## Contributing
All contributions are highly encouraged! You can add new features,
report and fix existing bugs and write docs and tutorials.
Feel free to open issue or send pull request!

## Prerequisites
The required dependencies to build ```vprof``` from source code:
 * Python 2.7, Python 3.4 or Python 3.5
 * `pip`
 * `npm` >= 3.3.12

`npm` is needed to build `vprof` from sources only.

## Dependencies
All Python and `npm` module dependencies are listed in `package.json` and `requirements.txt`.

## Installation
`vprof` can be installed from PyPI

```sh
pip install vprof
```

To build `vprof` from sources, clone this repository and execute

```sh
python setup.py deps_install && python setup.py build_ui && python setup.py install
```

To install just `vprof` dependencies, run

```sh
python setup.py deps_install
```

## Usage

```sh
vprof <modes> <test_program>
```
Supported modes:

* `c` - flame graph. Renders running time visualization for `<test_program>`.
* `m` - memory graph. Shows memory usage during execution of each line of `<test_program>`.
* `h` - code heatmap. Shows number of executions of each line of code.

`<test_program>` can be Python source file (e.g. `testscript.py`), installed Python package (e.g. `runpy`) or path to package (e.g. `myproject/test_package`).

Use double quotes to run scripts with arguments:

```sh
vprof -c cmh -s "testscript.py --foo --bar"
```

Modes can be combined:

```sh
vprof -c cm -s testscript.py
```

`vprof` can also profile single functions. In order to do this,
launch `vprof` in remote mode:

```sh
vprof -r
```

`vprof` will open new tab in default web browser and then wait for stats.

To profile a function you can do:

```python
from vprof import profiler

def foo(arg1, arg2):
    ...

profiler.run(foo, 'cmh', args=(arg1, arg2), host='localhost', port=8000)
```

where `cmh` is profiling mode, `host` and `port` are hostname and port of `vprof` server launched in remote mode. Obtained stats will be rendered in new tab of default web browser, opened by `vprof -r` command.

You can check `vprof -h` for full list of supported parameters.

Also you can check `examples` directory for more profiling examples.

## Testing

Just run:

```sh
python setup.py test && python setup.py e2e_test
```

## License

BSD
