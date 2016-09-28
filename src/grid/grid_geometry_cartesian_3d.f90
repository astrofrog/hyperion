module grid_geometry_specific

  use type_grid_cell

  implicit none
  save

contains

  real(dp) function cell_width(cell, idir)
    implicit none
    type(grid_cell),intent(in) :: cell
    integer,intent(in) :: idir
  end function cell_width

end module grid_geometry_specific
