module type_grid_cell

  use type_grid

  implicit none
  private

  public :: grid_cell
  type grid_cell
     integer :: i1, i2, i3, ic
  end type grid_cell

  type(grid_cell),parameter,public :: invalid_cell = grid_cell(-1,-1,-1,-1)

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
     integer :: w1=0, w2=0, w3=0
  end type wall_id

contains

  type(wall_id) function add_wall(a,b) result(c)
    implicit none
    type(wall_id), intent(in) :: a,b
    c%w1 = a%w1 + b%w1
    c%w2 = a%w2 + b%w2
    c%w3 = a%w3 + b%w3
  end function add_wall

  logical function equal(a,b)
    implicit none
    type(grid_cell), intent(in) :: a,b
    equal = a%i1 == b%i1 .and. a%i2 == b%i2 .and. a%i3 == b%i3
  end function equal

end module type_grid_cell
