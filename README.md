# the-flash
Carnegie Mellon University Mobot Racing 2016

This repo only contains framework codes, interfaces between Mobot itself
and the computer, raw data processing and other utilities.

The core algorithms are currently closed source and under active research and
development.

## Team Members
Harvey Shi,
Matthew Zhao,
Elias Lu,
Steven Yang,
Stefen Zhu

## Installation Instructions
Make sure you have the correct paths in your environment.
For example, sometimes you have pip2 directing to a python2
pip and use python2 instead of python.

### Get [Anaconda2]

### Install opencv3 for python2
```sh
$ conda install opencv
```
### Install rpyc for remote object sharing
Make sure you have pip for anaconda in PATH

You can check this by running python in terminal and see if anaconda is running.

You should see this:

> Python 2.7.11 |Anaconda 2.4.1 (x86_64)|

```sh
$ pip install rpyc
```

### Install PIL (Python Imaging Library)
For Mac Users:

```sh
$ sudo -H pip install Pillow
```

For Windows Users:

You need to install image library for PIL.
Do this in Administrator Command Prompt:
```sh
$ pip uninstall Pillow
$ pip install image
```

### Clone repo to your computer
```sh
$ git clone https://github.com/harveybia/the-flash.git
```
You are good to go.

[Anaconda2]: <https://www.continuum.io/downloads>
