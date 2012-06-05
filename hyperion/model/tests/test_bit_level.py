# The purpose of these tests is to check that the results produced by
# Hyperion agree at the bit-level. The data for these tests will need to be
# changed if algorithms are updated, and bugs are fixed, but otherwise there
# is no reason we should expect a change in results from one commit to the
# next. Since these files take place, we should minimize the number of tests
# to run.

import os
import itertools

import h5py
import pytest
import numpy as np

import cPickle as pickle

from .test_helpers import random_filename
from .. import Model
from ...util.constants import pc, lsun
from ...grid import CartesianGrid, CylindricalPolarGrid, SphericalPolarGrid, AMRGrid, OctreeGrid

GRID_TYPES = ['car', 'cyl', 'sph', 'amr', 'oct']

DATA = os.path.join(os.path.dirname(__file__), 'data')

generate_reference = pytest.mark.generate_reference


def setup_all_grid_types(self, u, d):
    '''
    All grids are guaranteed to cover the volume from -u to u in x, y, z
    '''

    np.random.seed(141412)

    self.grid = {}

    # Cartesian
    x = np.linspace(-u, u, 8)
    y = np.linspace(-u, u, 6)
    z = np.linspace(-u, u, 4)
    self.grid['car'] = CartesianGrid(x, y, z)

    # Cylindrical polar
    w = np.linspace(0., 2. * u, 8)
    z = np.linspace(-u, u, 4)
    p = np.linspace(0., 2. * np.pi, 6)
    self.grid['cyl'] = CylindricalPolarGrid(w, z, p)

    # Spherical polar
    r = np.linspace(0., 3. * u, 6)
    t = np.linspace(0., np.pi, 8)
    p = np.linspace(0., 2. * np.pi, 4)
    self.grid['sph'] = SphericalPolarGrid(r, t, p)

    # AMR
    self.grid['amr'] = AMRGrid()
    level = self.grid['amr'].add_level()
    grid = level.add_grid()
    grid.xmin, grid.xmax = -u, u
    grid.ymin, grid.ymax = -u, u
    grid.zmin, grid.zmax = -u, u
    grid.nx, grid.ny, grid.nz = 8, 6, 4
    grid.quantities['density'] = np.random.random((4, 6, 8)) * d

    # Octree
    refined = [1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
               0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0]
    self.grid['oct'] = OctreeGrid(0., 0., 0., u, u, u, np.array(refined).astype(bool))

    # Set up initial densities
    self.density = {}
    self.density['car'] = np.random.random(self.grid['car'].shape) * d
    self.density['cyl'] = np.random.random(self.grid['cyl'].shape) * d
    self.density['sph'] = np.random.random(self.grid['sph'].shape) * d
    self.density['amr'] = self.grid['amr']['density']
    self.density['oct'] = np.random.random(len(refined)) * d


def function_name():
    import sys
    import inspect
    caller = sys._getframe(1)
    args, _, _, values = inspect.getargvalues(caller)
    name = [caller.f_code.co_name]
    for arg in args:
        if arg not in ['self', 'generate']:
            name += ["{0}={1}".format(arg, values[arg])]
    name = '.'.join(name)
    return name


def assert_output_matches(filename, reference):

    differences = []

    # Get items from file to compare
    groups, datasets, attributes = make_item_list(filename)

    # Read in reference from pickle
    ref = open(reference, 'rb')
    groups_ref = pickle.load(ref)
    datasets_ref = pickle.load(ref)
    attributes_ref = pickle.load(ref)

    # Order groups since order is not guaranteed
    groups.sort()
    groups_ref.sort()

    # Check that group lists are the same
    if groups != groups_ref:
        differences.append("Group lists do not match: found {0} but expected {1}".format(str(groups), str(groups_ref)))

    # Make ordered lists of the datasets to compare
    dataset_list = sorted(datasets.keys())
    dataset_ref_list = sorted(datasets_ref.keys())

    # Check whether the dataset lists are different
    if dataset_list != dataset_ref_list:
        differences.append("Dataset lists do not match: found {0} but expected {1}".format(str(dataset_list), str(dataset_ref_list)))
    else: # Check that hashes match
        for d in datasets:
            if datasets[d] != datasets_ref[d]:
                differences.append("Dataset hashes do not match: found {0}={1} but expected {0}={2}".format(d, datasets[d], datasets_ref[d]))

    # Make ordered lists of the attributes to compare
    attribute_list = sorted(attributes.keys())
    attribute_ref_list = sorted(attributes_ref.keys())

    # Check whether the attribute lists are different
    if attribute_list != attribute_ref_list:
        differences.append("Attribute lists do not match: found {0} but expected {1}".format(str(attribute_list), str(attribute_ref_list)))
    else: # Check that hashes match
        for a in attributes:
            if attributes[a] != attributes_ref[a]:
                differences.append("Attribute values do not match: found {0}={1} but expected {0}={2}".format(a, attributes[a], attributes_ref[a]))

    for item in differences:
        print(item)

    assert len(differences) == 0


def write_item_list(filename, filename_out):

    groups, datasets, attributes = make_item_list(filename)

    f = open(filename_out, 'wb')
    pickle.dump(groups, f, 2)
    pickle.dump(datasets, f, 2)
    pickle.dump(attributes, f, 2)
    f.close()


def type_cast(a):
    try:
        float(a)
        if float(a) == int(a):
            return int(a)
        else:
            return float(a)
    except:
        return str(a)


def make_item_list(filename):

    from hashlib import md5

    # List of attributes to exclude from checking (time-dependent)
    EXCLUDE_ATTR = ['date_started', 'date_ended', 'cpu_time', 'python_version', 'fortran_version']

    groups = []
    datasets = {}
    attributes = {}

    # Open file
    f = h5py.File(filename, 'r')

    # List datasets and groups in file
    def func(name, obj):
        if isinstance(obj, h5py.Dataset):
            a = np.array(obj)
            datasets[name] = md5(a).hexdigest()
        elif isinstance(obj, h5py.Group):
            groups.append(name)
    f.visititems(func)

    # Loop over all groups and datasets to check attributes
    for item in ['/'] + datasets.keys() + groups:

        # Find all attributes
        attr = f[item].attrs.keys()

        for a in attr:
            if a not in EXCLUDE_ATTR:
                attributes[a] = type_cast(f[item].attrs[a])

    return groups, datasets, attributes


class TestEnergy(object):

    def setup_class(self):
        setup_all_grid_types(self, pc, 1.e-20)
        self.dust_file = os.path.join(DATA, 'kmh_lite.hdf5')

    @generate_reference
    @pytest.mark.parametrize(('grid_type', 'sample_sources_evenly'), list(itertools.product(GRID_TYPES, [True, False])))
    def test_specific_energy(self, grid_type, sample_sources_evenly, generate=False):

        np.random.seed(12345)

        m = Model()
        m.set_grid(self.grid[grid_type])
        m.add_density_grid(self.density[grid_type], self.dust_file)

        for i in range(5):
            s = m.add_point_source()
            s.luminosity = np.random.random() * lsun
            s.temperature = np.random.uniform(2000., 10000.)
            s.position = np.random.uniform(-pc, pc, 3)

        m.set_n_photons(initial=1000, imaging=0)

        m.set_copy_input(False)

        m.set_sample_sources_evenly(sample_sources_evenly)

        m.conf.output.output_specific_energy = 'all'

        m.write(random_filename(), copy=False, absolute_paths=True)
        output_file = random_filename()
        m.run(output_file, overwrite=True)

        if generate:
            reference_file = os.path.join(generate, function_name() + ".pickle")
            write_item_list(output_file, reference_file)
            pytest.skip("Skipping test, since generating data")
        else:
            reference_file = os.path.join(DATA, function_name() + ".pickle")
            assert_output_matches(output_file, reference_file)

    @generate_reference
    @pytest.mark.parametrize(('grid_type', 'raytracing', 'sample_sources_evenly'), list(itertools.product(GRID_TYPES, [True, False], [True, False])))
    def test_peeloff(self, grid_type, raytracing, sample_sources_evenly, generate=False):

        np.random.seed(12345)

        m = Model()
        m.set_grid(self.grid[grid_type])
        m.add_density_grid(self.density[grid_type], self.dust_file)

        for i in range(5):
            s = m.add_point_source()
            s.luminosity = np.random.random() * lsun
            s.temperature = np.random.uniform(2000., 10000.)
            s.position = np.random.uniform(-pc, pc, 3)

        m.set_raytracing(raytracing)
        if raytracing:
            m.set_n_photons(initial=1000, imaging=5000, raytracing_sources=2000, raytracing_dust=3000)
        else:
            m.set_n_photons(initial=1000, imaging=5000)

        m.set_copy_input(False)

        m.set_sample_sources_evenly(sample_sources_evenly)

        i_p = m.add_peeled_images()
        i_p.set_wavelength_range(5, 0.05, 200.)
        i_p.set_viewing_angles([33.4, 110.], [65.4, 103.2])
        i_p.set_image_size(4, 5)
        i_p.set_image_limits(-0.8 * pc, 0.8 * pc, -pc, pc)
        i_p.set_aperture_range(5, 0.1 * pc, pc)

        i_p = m.add_peeled_images()
        i_p.set_wavelength_range(4, 0.05, 200.)
        i_p.set_viewing_angles([22.1], [203.2])
        i_p.set_image_size(6, 6)
        i_p.set_image_limits(-pc, pc, -pc, pc)
        i_p.set_aperture_range(2, 0.5 * pc, pc)
        i_p.set_track_origin('basic')

        i_p = m.add_peeled_images()
        i_p.set_wavelength_range(4, 0.05, 200.)
        i_p.set_viewing_angles([22.1], [203.2])
        i_p.set_image_size(6, 6)
        i_p.set_image_limits(-pc, pc, -pc, pc)
        i_p.set_aperture_range(2, 0.5 * pc, pc)
        i_p.set_track_origin('detailed')

        m.write(random_filename(), copy=False, absolute_paths=True)
        output_file = random_filename()
        m.run(output_file, overwrite=True)

        if generate:
            reference_file = os.path.join(generate, function_name() + ".pickle")
            write_item_list(output_file, reference_file)
            pytest.skip("Skipping test, since generating data")
        else:
            reference_file = os.path.join(DATA, function_name() + ".pickle")
            assert_output_matches(output_file, reference_file)