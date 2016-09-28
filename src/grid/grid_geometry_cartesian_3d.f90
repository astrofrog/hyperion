module grid_geometry_specific

  use type_photon
  use type_grid_cell
  use type_grid

  implicit none
  save

contains

  real function cell_width(cell, idir)
    implicit none
    type(grid_cell),intent(in) :: cell
    integer,intent(in) :: idir
    cell_width = 0.
  end function cell_width

end module grid_geometry_specific
