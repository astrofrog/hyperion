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

  public :: operator(+)
  interface operator(+)
     module procedure add_wall
  end interface operator(+)

  public :: wall_id
  type wall_id
     integer :: w1=0
  end type wall_id

contains

  type(wall_id) function add_wall(a,b) result(c)
    implicit none
    type(wall_id), intent(in) :: a,b
    c%w1 = a%w1 + b%w1
  end function add_wall

  logical function equal(a,b)
    implicit none
    type(grid_cell), intent(in) :: a,b
    equal = a%i1 == b%i1
  end function equal

end module type_grid_cell
