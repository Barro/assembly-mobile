#!/bin/sh

for prog in curl gcc make tar gzip bzip2; do
    if test -z "`which $prog`"; then
        echo "$prog is needed!"
        exit 1
    fi
done

PYTHON_VERSION="2.5.4"
SETUPTOOLS_VERSION="0.6c9"

ASMMOBILE_ROOT="`pwd`"
PACKAGES_ROOT="$ASMMOBILE_ROOT"/packages
PYTHON_ROOT="$ASMMOBILE_ROOT"/python

PYTHON_PACKAGE="http://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tar.bz2"
SETUPTOOLS_PACKAGE="http://pypi.python.org/packages/source/s/setuptools/setuptools-${SETUPTOOLS_VERSION}.tar.gz"

# Install Python
mkdir "$PACKAGES_ROOT"
cd "$PACKAGES_ROOT"
curl -s "$PYTHON_PACKAGE" | tar xvj
cd Python-"${PYTHON_VERSION}"/
./configure --prefix="$PYTHON_ROOT"
make
make install

# Install setuptools that provides easy_install
cd "$PACKAGES_ROOT"
curl "$SETUPTOOLS_PACKAGE" | tar xvz
cd setuptools-"$SETUPTOOLS_VERSION"
"$PYTHON_ROOT"/bin/python setup.py install

# Clean up installation packages
cd "$ASMMOBILE_ROOT"
rm -rf "$PACKAGES_ROOT"

# Install zc.buildout
"$PYTHON_ROOT"/bin/easy_install zc.buildout

# Compile this application
cd "$ASMMOBILE_ROOT"
"$PYTHON_ROOT"/bin/buildout
# Create zeodb directory
mkdir "$ASMMOBILE_ROOT"/parts/zeodb
