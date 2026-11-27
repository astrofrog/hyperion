! Fortran interface to the C layer around MPI (mpi_c.c)
!
! This module provides the subset of the MPI Fortran API that Hyperion uses,
! with the same names and calling conventions as the mpi module, but calls
! the MPI C API through mpi_c.c instead of using the Fortran bindings of the
! MPI library. The handles defined here (communicators, datatypes, reduction
! operations and requests) are codes understood by mpi_c.c, not the handles
! of the underlying MPI library, so they should only be passed to the
! routines in this module. The values of the constants must be kept in sync
! with the HYP_* values in mpi_c.c.
!
! Routines that take "choice" buffers (buffers of any type and rank) are
! declared as bind(C) interfaces with assumed-type, assumed-size buffers, so
! that the address of the buffer is passed to C. The NO_ARG_CHECK attribute
! (supported by gfortran and the Intel compilers) allows scalars and arrays
! of any rank to be passed for these, while keeping the other arguments
! type-checked.

module mpi_c

  use iso_c_binding, only : c_int, c_char

  implicit none
  private

  ! Communicators
  integer,parameter,public :: mpi_comm_world = 1
  integer,parameter,public :: mpi_comm_self = 2

  ! Datatypes
  integer,parameter,public :: mpi_integer4 = 1
  integer,parameter,public :: mpi_integer8 = 2
  integer,parameter,public :: mpi_real4 = 3
  integer,parameter,public :: mpi_real8 = 4
  integer,parameter,public :: mpi_logical = 5
  integer,parameter,public :: mpi_character = 6
  integer,parameter,public :: mpi_integer = 7
  integer,parameter,public :: mpi_real = 8
  integer,parameter,public :: mpi_double_precision = 9

  ! Reduction operations
  integer,parameter,public :: mpi_sum = 1
  integer,parameter,public :: mpi_min = 2
  integer,parameter,public :: mpi_max = 3
  integer,parameter,public :: mpi_prod = 4
  integer,parameter,public :: mpi_land = 5
  integer,parameter,public :: mpi_lor = 6

  ! Special ranks, tags and requests
  integer,parameter,public :: mpi_any_source = -2
  integer,parameter,public :: mpi_any_tag = -1
  integer,parameter,public :: mpi_proc_null = -3
  integer,parameter,public :: mpi_request_null = 0

  ! Status (the source, tag and error are at the indices given below)
  integer,parameter,public :: mpi_status_size = 6
  integer,parameter,public :: mpi_source = 1
  integer,parameter,public :: mpi_tag = 2
  integer,parameter,public :: mpi_error = 3

  ! Statuses are never returned by mpi_waitall, so this is only a placeholder
  integer,parameter,public :: mpi_statuses_ignore(mpi_status_size, 1) = 0

  ! Other constants
  integer,parameter,public :: mpi_success = 0
  integer,parameter,public :: mpi_max_processor_name = 256

  public :: mpi_init
  public :: mpi_finalize
  public :: mpi_comm_rank
  public :: mpi_comm_size
  public :: mpi_barrier
  public :: mpi_get_processor_name
  public :: mpi_bcast
  public :: mpi_reduce
  public :: mpi_allreduce
  public :: mpi_send
  public :: mpi_recv
  public :: mpi_isend
  public :: mpi_irecv
  public :: mpi_test
  public :: mpi_request_free
  public :: mpi_waitall

  interface

     subroutine hyp_mpi_init(integer_size, logical_size, real_size, double_size, ierror) bind(C, name='hyp_mpi_init')
       import :: c_int
       integer(c_int),intent(in) :: integer_size, logical_size, real_size, double_size
       integer(c_int),intent(out) :: ierror
     end subroutine hyp_mpi_init

     subroutine mpi_finalize(ierror) bind(C, name='hyp_mpi_finalize')
       import :: c_int
       integer(c_int),intent(out) :: ierror
     end subroutine mpi_finalize

     subroutine mpi_comm_rank(comm, rank, ierror) bind(C, name='hyp_mpi_comm_rank')
       import :: c_int
       integer(c_int),intent(in) :: comm
       integer(c_int),intent(out) :: rank, ierror
     end subroutine mpi_comm_rank

     subroutine mpi_comm_size(comm, size, ierror) bind(C, name='hyp_mpi_comm_size')
       import :: c_int
       integer(c_int),intent(in) :: comm
       integer(c_int),intent(out) :: size, ierror
     end subroutine mpi_comm_size

     subroutine mpi_barrier(comm, ierror) bind(C, name='hyp_mpi_barrier')
       import :: c_int
       integer(c_int),intent(in) :: comm
       integer(c_int),intent(out) :: ierror
     end subroutine mpi_barrier

     subroutine hyp_mpi_get_processor_name(name, name_len, resultlen, ierror) bind(C, name='hyp_mpi_get_processor_name')
       import :: c_int, c_char
       character(kind=c_char),intent(out) :: name(*)
       integer(c_int),intent(in) :: name_len
       integer(c_int),intent(out) :: resultlen, ierror
     end subroutine hyp_mpi_get_processor_name

     subroutine mpi_bcast(buffer, count, datatype, root, comm, ierror) bind(C, name='hyp_mpi_bcast')
       import :: c_int
       !GCC$ ATTRIBUTES NO_ARG_CHECK :: buffer
       !DEC$ ATTRIBUTES NO_ARG_CHECK :: buffer
       type(*),dimension(*) :: buffer
       integer(c_int),intent(in) :: count, datatype, root, comm
       integer(c_int),intent(out) :: ierror
     end subroutine mpi_bcast

     subroutine mpi_reduce(sendbuf, recvbuf, count, datatype, op, root, comm, ierror) bind(C, name='hyp_mpi_reduce')
       import :: c_int
       !GCC$ ATTRIBUTES NO_ARG_CHECK :: sendbuf, recvbuf
       !DEC$ ATTRIBUTES NO_ARG_CHECK :: sendbuf, recvbuf
       type(*),dimension(*),intent(in) :: sendbuf
       type(*),dimension(*) :: recvbuf
       integer(c_int),intent(in) :: count, datatype, op, root, comm
       integer(c_int),intent(out) :: ierror
     end subroutine mpi_reduce

     subroutine mpi_allreduce(sendbuf, recvbuf, count, datatype, op, comm, ierror) bind(C, name='hyp_mpi_allreduce')
       import :: c_int
       !GCC$ ATTRIBUTES NO_ARG_CHECK :: sendbuf, recvbuf
       !DEC$ ATTRIBUTES NO_ARG_CHECK :: sendbuf, recvbuf
       type(*),dimension(*),intent(in) :: sendbuf
       type(*),dimension(*) :: recvbuf
       integer(c_int),intent(in) :: count, datatype, op, comm
       integer(c_int),intent(out) :: ierror
     end subroutine mpi_allreduce

     subroutine mpi_send(buf, count, datatype, dest, tag, comm, ierror) bind(C, name='hyp_mpi_send')
       import :: c_int
       !GCC$ ATTRIBUTES NO_ARG_CHECK :: buf
       !DEC$ ATTRIBUTES NO_ARG_CHECK :: buf
       type(*),dimension(*),intent(in) :: buf
       integer(c_int),intent(in) :: count, datatype, dest, tag, comm
       integer(c_int),intent(out) :: ierror
     end subroutine mpi_send

     subroutine mpi_recv(buf, count, datatype, source, tag, comm, status, ierror) bind(C, name='hyp_mpi_recv')
       import :: c_int, mpi_status_size
       !GCC$ ATTRIBUTES NO_ARG_CHECK :: buf
       !DEC$ ATTRIBUTES NO_ARG_CHECK :: buf
       type(*),dimension(*) :: buf
       integer(c_int),intent(in) :: count, datatype, source, tag, comm
       integer(c_int),intent(out) :: status(mpi_status_size), ierror
     end subroutine mpi_recv

     ! The buffers of non-blocking routines must not be copied by the
     ! compiler, so they should be contiguous (in practice they are scalars
     ! or array elements here)
     subroutine mpi_isend(buf, count, datatype, dest, tag, comm, request, ierror) bind(C, name='hyp_mpi_isend')
       import :: c_int
       !GCC$ ATTRIBUTES NO_ARG_CHECK :: buf
       !DEC$ ATTRIBUTES NO_ARG_CHECK :: buf
       type(*),dimension(*),intent(in) :: buf
       integer(c_int),intent(in) :: count, datatype, dest, tag, comm
       integer(c_int),intent(out) :: request, ierror
     end subroutine mpi_isend

     subroutine mpi_irecv(buf, count, datatype, source, tag, comm, request, ierror) bind(C, name='hyp_mpi_irecv')
       import :: c_int
       !GCC$ ATTRIBUTES NO_ARG_CHECK :: buf
       !DEC$ ATTRIBUTES NO_ARG_CHECK :: buf
       type(*),dimension(*) :: buf
       integer(c_int),intent(in) :: count, datatype, source, tag, comm
       integer(c_int),intent(out) :: request, ierror
     end subroutine mpi_irecv

     subroutine hyp_mpi_test(request, flag, status, ierror) bind(C, name='hyp_mpi_test')
       import :: c_int, mpi_status_size
       integer(c_int),intent(inout) :: request
       integer(c_int),intent(out) :: flag
       integer(c_int),intent(inout) :: status(mpi_status_size)
       integer(c_int),intent(out) :: ierror
     end subroutine hyp_mpi_test

     subroutine mpi_request_free(request, ierror) bind(C, name='hyp_mpi_request_free')
       import :: c_int
       integer(c_int),intent(inout) :: request
       integer(c_int),intent(out) :: ierror
     end subroutine mpi_request_free

     subroutine hyp_mpi_waitall(count, requests, ierror) bind(C, name='hyp_mpi_waitall')
       import :: c_int
       integer(c_int),intent(in) :: count
       integer(c_int),intent(inout) :: requests(*)
       integer(c_int),intent(out) :: ierror
     end subroutine hyp_mpi_waitall

  end interface

contains

  subroutine mpi_init(ierror)
    ! Pass the sizes of the default types to C so that the datatypes for
    ! them (mpi_integer, mpi_logical, mpi_real, mpi_double_precision) match
    ! whatever kinds the compiler uses by default
    implicit none
    integer,intent(out) :: ierror
    call hyp_mpi_init(int(storage_size(0) / 8, c_int), &
         &            int(storage_size(.true.) / 8, c_int), &
         &            int(storage_size(0.) / 8, c_int), &
         &            int(storage_size(0.d0) / 8, c_int), ierror)
  end subroutine mpi_init

  subroutine mpi_get_processor_name(name, resultlen, ierror)
    implicit none
    character(len=*),intent(out) :: name
    integer,intent(out) :: resultlen, ierror
    character(kind=c_char) :: buffer(len(name))
    integer :: i
    call hyp_mpi_get_processor_name(buffer, int(len(name), c_int), resultlen, ierror)
    do i=1,len(name)
       name(i:i) = buffer(i)
    end do
  end subroutine mpi_get_processor_name

  subroutine mpi_test(request, flag, status, ierror)
    implicit none
    integer,intent(inout) :: request
    logical,intent(out) :: flag
    integer,intent(inout) :: status(mpi_status_size)
    integer,intent(out) :: ierror
    integer(c_int) :: cflag
    call hyp_mpi_test(request, cflag, status, ierror)
    flag = cflag /= 0
  end subroutine mpi_test

  subroutine mpi_waitall(count, requests, statuses, ierror)
    ! Only mpi_statuses_ignore is supported for the statuses, which are not
    ! returned
    implicit none
    integer,intent(in) :: count
    integer,intent(inout) :: requests(*)
    integer,intent(in) :: statuses(mpi_status_size, *)
    integer,intent(out) :: ierror
    call hyp_mpi_waitall(count, requests, ierror)
  end subroutine mpi_waitall

end module mpi_c
