"""
Locate the Hyperion Fortran binaries and the MPI launcher to use with them.

The binaries are looked for, in order:

1. In the directory given by the ``HYPERION_BIN_DIR`` environment variable,
   or by the ``dir`` option in the ``[binaries]`` section of
   ``~/.hyperionrc``, if either is set.
2. In the ``hyperion-fortran`` package, if it is installed.
3. On the ``PATH``, which is where binaries compiled from source are
   installed.

The binaries from the ``hyperion-fortran`` package, which match the version
of the Python package, take precedence over any (possibly older) binaries on
the ``PATH``. To use binaries compiled from source, for example on a cluster,
either do not install ``hyperion-fortran`` or set ``HYPERION_BIN_DIR``.
"""

import os
import shutil
from configparser import ConfigParser

__all__ = ['find_binary', 'find_mpi_launcher']


def _read_config():
    config = ConfigParser()
    config.read(os.path.expanduser('~/.hyperionrc'))
    return config


def _explicit_bin_dir():
    if os.environ.get('HYPERION_BIN_DIR'):
        return os.environ['HYPERION_BIN_DIR']
    config = _read_config()
    if config.has_option('binaries', 'dir'):
        return os.path.expanduser(config.get('binaries', 'dir'))
    return None


def _package_bin_dir():
    try:
        import hyperion_fortran
    except ImportError:
        return None
    return hyperion_fortran.bin_dir()


def find_binary(name):
    """
    Find a Hyperion binary, such as ``hyperion_sph`` or ``hyperion_sph_mpi``.

    Parameters
    ----------
    name : str
        The name of the binary

    Returns
    -------
    path : str
        The full path to the binary
    source : str
        Where the binary was found: ``'explicit'``, ``'path'`` or
        ``'package'``

    Raises
    ------
    FileNotFoundError
        If the binary cannot be found anywhere.
    """

    bin_dir = _explicit_bin_dir()
    if bin_dir is not None:
        path = os.path.join(bin_dir, name)
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path, 'explicit'
        raise FileNotFoundError(f"{name} not found in {bin_dir} (set by "
                                "HYPERION_BIN_DIR or ~/.hyperionrc)")

    bin_dir = _package_bin_dir()
    if bin_dir is not None:
        path = os.path.join(bin_dir, name)
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path, 'package'

    path = shutil.which(name)
    if path is not None:
        return path, 'path'

    raise FileNotFoundError(f"Could not find the Hyperion binary {name} - see the "
                            "installation instructions for how to compile and "
                            "install the Fortran code")


def find_mpi_launcher(source):
    """
    Find the command to launch the MPI binaries with.

    Parameters
    ----------
    source : str
        Where the MPI binary was found, as returned by `find_binary`. Binaries
        from the ``hyperion-fortran`` package are always launched with the
        ``mpiexec`` matching the MPI library they use, since a launcher from
        another MPI implementation does not work with them.

    Returns
    -------
    command : str
        The launcher command (which may include options)
    """

    if source == 'package':
        import hyperion_fortran
        return hyperion_fortran.mpi_launcher()

    config = _read_config()
    if config.has_option('mpi', 'command'):
        return config.get('mpi', 'command')

    for launcher in ('mpirun', 'mpiexec'):
        if shutil.which(launcher) is not None:
            return launcher

    raise FileNotFoundError("Cannot find mpirun or mpiexec")
