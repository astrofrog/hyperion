import os
import sys
import types

import pytest

from .. import binaries
from ..binaries import find_binary, find_mpi_launcher


def make_binary(directory, name):
    path = directory.join(name)
    path.write('#!/bin/sh\n')
    os.chmod(path.strpath, 0o755)
    return path.strpath


@pytest.fixture
def isolated(tmpdir, monkeypatch):
    # Start from an environment with no binaries anywhere: an empty PATH, no
    # HYPERION_BIN_DIR, a home directory without ~/.hyperionrc, and no
    # hyperion_fortran package
    monkeypatch.setenv('PATH', tmpdir.mkdir('empty').strpath)
    monkeypatch.delenv('HYPERION_BIN_DIR', raising=False)
    monkeypatch.setenv('HOME', tmpdir.mkdir('home').strpath)
    monkeypatch.setitem(sys.modules, 'hyperion_fortran', None)
    return tmpdir


def fake_package(monkeypatch, bin_dir, launcher='mpiexec-from-package'):
    module = types.ModuleType('hyperion_fortran')
    module.bin_dir = lambda: bin_dir
    module.mpi_launcher = lambda: launcher
    monkeypatch.setitem(sys.modules, 'hyperion_fortran', module)


def test_not_found(isolated):
    with pytest.raises(FileNotFoundError) as exc:
        find_binary('hyperion_sph')
    assert "installation instructions" in exc.value.args[0]


def test_package(isolated, monkeypatch):
    package = isolated.mkdir('package')
    expected = make_binary(package, 'hyperion_sph')
    fake_package(monkeypatch, package.strpath)
    assert find_binary('hyperion_sph') == (expected, 'package')


def test_path(isolated, monkeypatch):
    source = isolated.mkdir('source')
    expected = make_binary(source, 'hyperion_sph')
    monkeypatch.setenv('PATH', source.strpath)
    assert find_binary('hyperion_sph') == (expected, 'path')


def test_package_takes_precedence_over_path(isolated, monkeypatch):
    # Binaries on the PATH may be from an older version, so the ones from the
    # package are used if it is installed
    source = isolated.mkdir('source')
    make_binary(source, 'hyperion_sph')
    monkeypatch.setenv('PATH', source.strpath)
    package = isolated.mkdir('package')
    expected = make_binary(package, 'hyperion_sph')
    fake_package(monkeypatch, package.strpath)
    assert find_binary('hyperion_sph') == (expected, 'package')


def test_package_missing_binary_falls_back_to_path(isolated, monkeypatch):
    # For example if the package does not include MPI binaries
    fake_package(monkeypatch, isolated.mkdir('package').strpath)
    source = isolated.mkdir('source')
    expected = make_binary(source, 'hyperion_sph_mpi')
    monkeypatch.setenv('PATH', source.strpath)
    assert find_binary('hyperion_sph_mpi') == (expected, 'path')


@pytest.mark.parametrize('setting', ['environment', 'config'])
def test_explicit_takes_precedence(isolated, monkeypatch, setting):
    source = isolated.mkdir('source')
    make_binary(source, 'hyperion_sph')
    monkeypatch.setenv('PATH', source.strpath)
    package = isolated.mkdir('package')
    make_binary(package, 'hyperion_sph')
    fake_package(monkeypatch, package.strpath)
    explicit = isolated.mkdir('explicit')
    expected = make_binary(explicit, 'hyperion_sph')
    if setting == 'environment':
        monkeypatch.setenv('HYPERION_BIN_DIR', explicit.strpath)
    else:
        isolated.join('home', '.hyperionrc').write(f'[binaries]\ndir = {explicit.strpath}\n')
    assert find_binary('hyperion_sph') == (expected, 'explicit')


def test_explicit_missing_binary(isolated, monkeypatch):
    # If a directory is given explicitly, binaries elsewhere are not used
    source = isolated.mkdir('source')
    make_binary(source, 'hyperion_sph')
    monkeypatch.setenv('PATH', source.strpath)
    monkeypatch.setenv('HYPERION_BIN_DIR', isolated.mkdir('explicit').strpath)
    with pytest.raises(FileNotFoundError) as exc:
        find_binary('hyperion_sph')
    assert "HYPERION_BIN_DIR" in exc.value.args[0]


def test_launcher_for_package_binaries(isolated, monkeypatch):
    # Binaries from the package always use the launcher from the package,
    # even if another launcher is on the PATH or set in ~/.hyperionrc
    fake_package(monkeypatch, isolated.strpath)
    make_binary(isolated.join('empty'), 'mpirun')
    isolated.join('home', '.hyperionrc').write('[mpi]\ncommand = mpirun --custom\n')
    assert find_mpi_launcher('package') == 'mpiexec-from-package'


def test_launcher_for_other_binaries(isolated):
    with pytest.raises(FileNotFoundError):
        find_mpi_launcher('path')
    make_binary(isolated.join('empty'), 'mpiexec')
    assert find_mpi_launcher('path') == 'mpiexec'
    make_binary(isolated.join('empty'), 'mpirun')
    assert find_mpi_launcher('path') == 'mpirun'
    isolated.join('home', '.hyperionrc').write('[mpi]\ncommand = mpirun --custom\n')
    assert find_mpi_launcher('explicit') == 'mpirun --custom'


def test_module_docstring_matches_order():
    # Keep the documented order in sync with the code
    doc = binaries.__doc__
    assert doc.index('HYPERION_BIN_DIR') < doc.index('hyperion-fortran') < doc.index('``PATH``')
