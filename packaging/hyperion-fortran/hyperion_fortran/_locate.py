import os
import shlex
import sys
from importlib import metadata

__all__ = ['bin_dir', 'mpi_launcher']


def bin_dir():
    """
    Return the directory containing the Hyperion binaries in this package.
    """
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bin')


def mpi_launcher():
    """
    Return the command to launch the MPI binaries in this package with.

    This is the mpiexec from the mpich package, which provides the MPI
    standard ABI library (libmpi_abi) that the binaries are linked against.
    The directory containing that library is passed on to the MPI processes
    by mpiexec itself, since it is not on the default library search path,
    and setting the search path through the environment of the launching
    process is not reliable (macOS removes these variables when starting
    programs through the shell).
    """
    try:
        files = metadata.files('mpich')
    except metadata.PackageNotFoundError:
        raise FileNotFoundError("The MPI binaries in hyperion-fortran need the mpich "
                                "package - install it with "
                                "'pip install hyperion-fortran[mpi]'") from None
    mpiexec = lib_dir = None
    for f in files or []:
        if f.name == 'mpiexec' and f.parent.name == 'bin':
            mpiexec = os.path.normpath(f.locate())
        elif f.name.startswith('libmpi_abi.'):
            lib_dir = os.path.dirname(os.path.normpath(f.locate()))
    if mpiexec is None or lib_dir is None:
        raise FileNotFoundError("Could not find mpiexec and libmpi_abi in the mpich package")
    variable = 'DYLD_LIBRARY_PATH' if sys.platform == 'darwin' else 'LD_LIBRARY_PATH'
    command = f'{shlex.quote(mpiexec)} -genv {variable} {shlex.quote(lib_dir)}'
    # The MPI library from the mpich package is used for runs on a single
    # machine, so restrict its UCX communication layer to shared memory, since
    # UCX can otherwise fail to start on machines with network devices that
    # only partly support InfiniBand (unless UCX_TLS is already set)
    if 'UCX_TLS' not in os.environ:
        command += ' -genv UCX_TLS self,sm'
    return command
