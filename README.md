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

### For Mac Users:

#### Get [homebrew]
```sh
/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
```

#### Install python2 in homebrew
```sh
$ brew install python
$ brew link --overwrite python
```

#### Install opencv3 for python2
```sh
$ brew install opencv
```

#### Add /usr/local/bin into your path

Add the following line at the end of your .bash_profile

```sh
PATH="/usr/local/bin:${PATH}"
```

### For Windows Users:

#### Install OpenCV for python2

(The method could be found on internet, just add symbolic link would work)

You can just download complied binary code and make symbolic link
(not shortcut) in site-packages folder in python27 installation destination.

### Install rpyc for remote object sharing
Make sure you have pip for brew python in PATH (not the system default one)

You can check this by using "which" command
```sh
$ which python
```

You should see:

> /usr/local/bin/python

```sh
$ pip install rpyc
```

### Install PIL (Python Imaging Library)
For Mac Users:

(Sometimes this package is already included when installing OpenCV
with brew)

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
$ git clone https://github.com/harveybia/the-flash-sudo.git
```
You are good to go.

[homebrew]: <http://brew.sh>
