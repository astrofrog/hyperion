# Check that the binaries in an installed hyperion-fortran wheel work, by
# running a small model with the serial binary and, if the MPI binaries and
# the mpich package are installed, with two MPI processes. This is run by the
# wheel building workflow after installing each wheel.

import os
import sys
import tempfile

import numpy as np

from hyperion.dust import IsotropicDust
from hyperion.model import Model
from hyperion.util.binaries import find_binary
from hyperion.util.constants import au, lsun, rsun


def small_model(directory):
    nu = np.logspace(9, 16, 50)
    dust = IsotropicDust(nu, np.repeat(0.5, 50), np.repeat(1., 50))
    dust.set_lte_emissivities(n_temp=10, temp_min=10., temp_max=1000.)
    m = Model()
    m.set_spherical_polar_grid(np.linspace(0., 10. * au, 21), [0., np.pi], [0., 2. * np.pi])
    m.add_density_grid(np.ones(m.grid.shape) * 1.e-20, dust)
    source = m.add_spherical_source()
    source.radius = rsun
    source.luminosity = lsun
    source.temperature = 6000.
    sed = m.add_peeled_images(sed=True, image=False)
    sed.set_viewing_angles([45.], [0.])
    sed.set_wavelength_range(20, 0.1, 1000.)
    m.set_n_initial_iterations(2)
    m.set_n_photons(initial=20000, imaging=20000)
    m.set_seed(-12345)
    m.write(os.path.join(directory, 'model.rtin'))
    return m


def check(directory, name, **kwargs):
    m = small_model(directory)
    binary, source = find_binary(name)
    if source != 'package':
        sys.exit(f"{name} was found at {binary} rather than in hyperion-fortran")
    output = m.run(os.path.join(directory, name + '.rtout'), **kwargs)
    flux = output.get_sed().val
    if not np.all(np.isfinite(flux)) or not np.any(flux > 0):
        sys.exit(f"{name} gave an invalid SED")
    print(f"{name}: OK")


with tempfile.TemporaryDirectory() as directory:
    check(directory, 'hyperion_sph')
    try:
        import importlib.metadata
        importlib.metadata.distribution('mpich')
    except importlib.metadata.PackageNotFoundError:
        print("mpich package not installed, not checking the MPI binaries")
    else:
        check(directory, 'hyperion_sph_mpi', mpi=True, n_processes=2)
