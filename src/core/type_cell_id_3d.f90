module type_grid_cell

  use type_grid

  implicit none
  private

  public :: grid_cell
  type grid_cell
     integer :: i1
  end type grid_cell

  public :: operator(.eq.)
  interface operator(.eq.)
     module procedure equal
  end interface operator(.eq.)


  public :: wall_id
  type wall_id
     integer :: w1=0
  end type wall_id

contains



  logical function equal(a,b)
    implicit none
    type(grid_cell), intent(in) :: a,b
    equal = a%i1 == b%i1
  end function equal

end module type_grid_cell
