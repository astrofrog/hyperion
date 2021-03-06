About
=====

Hyperion is a 3D Monte-Carlo radiation transfer code - see http://www.hyperion-rt.org
for more details.

Downloading
===========

Stable releases can be found at:

    https://github.com/hyperion-rt/hyperion/downloads

To download from the git repository, use:

    git clone git@github.com:hyperion-rt/hyperion.git
    cd hyperion
    git submodule init
    git submodule update

Documentation
=============

To build the HTML documentation:

    cd docs
    make html

The documentation will then be available at `docs/build/html`. Note that <a
href="cd documentation">Sphinx</a> is required to build the documentation

Updating
========

To update your clone of the git repository, use:

    git pull
    git submodule update

