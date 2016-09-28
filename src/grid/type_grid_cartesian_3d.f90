module type_grid

  use core_lib

  implicit none
  save

  private

  public :: grid_geometry_desc
  type grid_geometry_desc

     character(len=32) :: id


  end type grid_geometry_desc

end module type_grid
