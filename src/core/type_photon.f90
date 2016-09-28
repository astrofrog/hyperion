! Verified and cleaned 13/09/08

module type_photon

  use core_lib
  use type_grid_cell

  implicit none
  save

  private
  public :: photon

  type photon

     type(grid_cell) :: icell

  end type photon

end module type_photon
