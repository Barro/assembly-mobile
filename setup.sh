#!/bin/sh

set -eu

for prog in curl gcc make tar gzip bzip2; do
    if test -z "$(which $prog)"; then
        echo "$prog is needed!"
        exit 1
    fi
done

if test ! -f base.cfg; then
    echo "Should we use 'devel' or 'production' version of base.cfg?"
    read CFG_VERSION
    CFG_BASE=base.cfg."$CFG_VERSION"
    if test -f "$CFG_BASE"; then
        cp "$CFG_BASE" base.cfg
    else
        echo "File '${CFG_BASE}' does not exist."
        exit 1
    fi
fi

PYTHON_VERSION=2.7.12

ASMMOBILE_ROOT=$(pwd)
mkdir -p extends-cache
PACKAGES_ROOT="$ASMMOBILE_ROOT"/packages
PYTHON_ROOT="$ASMMOBILE_ROOT"/python

PYTHON_PACKAGE="https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tar.xz"

# Install Python
mkdir -p "$PACKAGES_ROOT"
cd "$PACKAGES_ROOT"
echo "Downloading $PYTHON_PACKAGE"
curl -ko "Python-${PYTHON_VERSION}.tar.xz" "$PYTHON_PACKAGE"
tar xvf "Python-${PYTHON_VERSION}.tar.xz"
cd Python-"${PYTHON_VERSION}"/
./configure --prefix="$PYTHON_ROOT"
make -j "$(nproc)"
make install

# Clean up installation packages:
cd "$ASMMOBILE_ROOT"
rm -rf "$PACKAGES_ROOT"

# Bootstrap necessary eggs:
cd "$ASMMOBILE_ROOT"
"$PYTHON_ROOT"/bin/python bootstrap.py

# Compile this application:
cd "$ASMMOBILE_ROOT"
"$ASMMOBILE_ROOT"/bin/buildout
