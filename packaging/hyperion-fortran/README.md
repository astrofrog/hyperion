# hyperion-fortran

Compiled Fortran binaries for the [Hyperion](https://www.hyperion-rt.org)
radiative transfer code, installed with `pip install hyperion[fortran]`.

When this package is installed, the `hyperion` Python package uses these
binaries rather than any found on the `PATH`. To use binaries compiled from
source instead, for example on a cluster, do not install this package, or set
`HYPERION_BIN_DIR`: see `hyperion.util.binaries`.
