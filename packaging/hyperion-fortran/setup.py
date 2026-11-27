# Build the Hyperion Fortran binaries with the configure script and Makefile
# at the root of the repository, and include them in the package. The
# binaries do not depend on the version of Python, so the wheel is tagged as
# py3-none-<platform>.
#
# Set HYPERION_FORTRAN_MPI=1 to also build the MPI binaries. These are built
# against the MPI standard ABI library (libmpi_abi) from the mpich package on
# PyPI, which is a build requirement. At run time they use the library from
# the mpich package installed alongside this one, which mpi_launcher() tells
# mpiexec about (see _locate.py), and when repairing the wheel libmpi_abi
# should be excluded, e.g. with auditwheel repair --exclude libmpi_abi.so.1.

import os
import shutil
import subprocess
import sys

from setuptools import Distribution, setup
from setuptools_scm import get_version
from setuptools.command.build_py import build_py
from wheel.bdist_wheel import bdist_wheel

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


class BuildBinaries(build_py):

    def run(self):
        super().run()
        mpi = os.environ.get('HYPERION_FORTRAN_MPI') == '1'
        configure = ['./configure', *os.environ.get('HYPERION_CONFIGURE_FLAGS', '').split()]
        targets = ['serial']
        if mpi:
            configure += ['--enable-mpi-abi', 'MPICC=' + os.path.join(sys.prefix, 'bin', 'mpicc_abi')]
            targets.append('mpi')
        subprocess.check_call(configure, cwd=ROOT)
        # Always rebuild everything (-B), since binaries left over from a build
        # with different configure options (e.g. another MPI library) would
        # otherwise be considered up to date
        subprocess.check_call(['make', '-B', '-j4', *targets], cwd=ROOT)
        target_dir = os.path.join(self.build_lib, 'hyperion_fortran', 'bin')
        os.makedirs(target_dir, exist_ok=True)
        for name in sorted(os.listdir(os.path.join(ROOT, 'bin'))):
            path = os.path.join(ROOT, 'bin', name)
            # Only copy the binaries themselves, not e.g. the .dSYM debug
            # symbol directories that the compilers create on macOS
            if name.startswith('hyperion_') and os.path.isfile(path):
                shutil.copy2(path, target_dir)


class BinaryDistribution(Distribution):
    # The package contains compiled binaries, so the wheel is platform-specific

    def has_ext_modules(self):
        return True


class PlatformWheel(bdist_wheel):

    def get_tag(self):
        _, _, platform = super().get_tag()
        return 'py3', 'none', platform


# The binaries and the Python package have to match (they share the format of
# the input and output files), and are released with the same version, so
# require exactly the version of hyperion that the binaries were built from.
# Installing hyperion[fortran] then always gives matching versions.
VERSION = get_version(root=ROOT)

setup(distclass=BinaryDistribution,
      install_requires=[f'hyperion=={VERSION}'],
      cmdclass={'build_py': BuildBinaries, 'bdist_wheel': PlatformWheel})
