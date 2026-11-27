/* C layer between the Fortran code and the MPI C API.
 *
 * The Fortran code does not use the Fortran bindings of MPI (the mpi module,
 * mpif90 and the MPI Fortran library). Instead, the mpi_c module (mpi_c.f90)
 * declares bind(C) interfaces to the functions below, which call the MPI C
 * API. This means that only an MPI C compiler and C library are needed, and
 * the code can be compiled against the standard MPI ABI (mpi_abi.h and
 * libmpi_abi), in which case the binaries work with any MPI library that
 * implements that ABI.
 *
 * Handles on the Fortran side are small integer codes defined in mpi_c.f90
 * (which must be kept in sync with the HYP_* values below), and are mapped
 * here to the MPI_Comm, MPI_Datatype and MPI_Op values. Requests are stored
 * in a table and the Fortran side sees the index into that table plus one,
 * with zero standing for MPI_REQUEST_NULL. All integer arguments are passed
 * by reference as C int, which is the default Fortran integer kind.
 */

#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Communicators */
#define HYP_COMM_WORLD 1
#define HYP_COMM_SELF 2

/* Datatypes */
#define HYP_INTEGER4 1
#define HYP_INTEGER8 2
#define HYP_REAL4 3
#define HYP_REAL8 4
#define HYP_LOGICAL 5
#define HYP_CHARACTER 6
#define HYP_INTEGER 7
#define HYP_REAL 8
#define HYP_DOUBLE_PRECISION 9

/* Reduction operations */
#define HYP_SUM 1
#define HYP_MIN 2
#define HYP_MAX 3
#define HYP_PROD 4
#define HYP_LAND 5
#define HYP_LOR 6

/* Special ranks and tags */
#define HYP_ANY_SOURCE -2
#define HYP_ANY_TAG -1
#define HYP_PROC_NULL -3

/* Layout of the Fortran status array */
#define HYP_STATUS_SIZE 6
#define HYP_SOURCE 0
#define HYP_TAG 1
#define HYP_ERROR 2

/* Datatypes matching the default Fortran integer, logical, real and double
 * precision types, set by hyp_mpi_init from the storage sizes of these types
 * so that compiler options that change the default kinds are handled. */
static MPI_Datatype default_integer = MPI_DATATYPE_NULL;
static MPI_Datatype default_logical = MPI_DATATYPE_NULL;
static MPI_Datatype default_real = MPI_DATATYPE_NULL;
static MPI_Datatype default_double = MPI_DATATYPE_NULL;

/* Table of active requests */
static MPI_Request *requests = NULL;
static int n_requests = 0;

static void fatal(const char *message, int value) {
  fprintf(stderr, "ERROR: mpi_c: %s (%d)\n", message, value);
  fflush(stderr);
  MPI_Abort(MPI_COMM_WORLD, 1);
  exit(1);
}

static MPI_Datatype integer_type(int size) {
  switch (size) {
  case 1: return MPI_INT8_T;
  case 2: return MPI_INT16_T;
  case 4: return MPI_INT32_T;
  case 8: return MPI_INT64_T;
  }
  fatal("unsupported size for Fortran integer or logical", size);
  return MPI_DATATYPE_NULL;
}

static MPI_Datatype real_type(int size) {
  if (size == (int)sizeof(float)) return MPI_FLOAT;
  if (size == (int)sizeof(double)) return MPI_DOUBLE;
  fatal("unsupported size for Fortran real", size);
  return MPI_DATATYPE_NULL;
}

static MPI_Comm comm(int handle) {
  switch (handle) {
  case HYP_COMM_WORLD: return MPI_COMM_WORLD;
  case HYP_COMM_SELF: return MPI_COMM_SELF;
  }
  fatal("unknown communicator handle", handle);
  return MPI_COMM_NULL;
}

static MPI_Datatype datatype(int handle) {
  switch (handle) {
  case HYP_INTEGER4: return MPI_INT32_T;
  case HYP_INTEGER8: return MPI_INT64_T;
  case HYP_REAL4: return MPI_FLOAT;
  case HYP_REAL8: return MPI_DOUBLE;
  case HYP_CHARACTER: return MPI_CHAR;
  case HYP_LOGICAL: if (default_logical != MPI_DATATYPE_NULL) return default_logical; break;
  case HYP_INTEGER: if (default_integer != MPI_DATATYPE_NULL) return default_integer; break;
  case HYP_REAL: if (default_real != MPI_DATATYPE_NULL) return default_real; break;
  case HYP_DOUBLE_PRECISION: if (default_double != MPI_DATATYPE_NULL) return default_double; break;
  default: fatal("unknown datatype handle", handle);
  }
  fatal("datatype used before mpi_init", handle);
  return MPI_DATATYPE_NULL;
}

/* Logical values are stored in integers, so the logical reductions on them
 * treat any non-zero value as true and return 1 for true. */
static MPI_Op op(int handle) {
  switch (handle) {
  case HYP_SUM: return MPI_SUM;
  case HYP_MIN: return MPI_MIN;
  case HYP_MAX: return MPI_MAX;
  case HYP_PROD: return MPI_PROD;
  case HYP_LAND: return MPI_LAND;
  case HYP_LOR: return MPI_LOR;
  }
  fatal("unknown operation handle", handle);
  return MPI_OP_NULL;
}

static int source(int rank) {
  if (rank == HYP_ANY_SOURCE) return MPI_ANY_SOURCE;
  if (rank == HYP_PROC_NULL) return MPI_PROC_NULL;
  return rank;
}

static int tag(int value) {
  return value == HYP_ANY_TAG ? MPI_ANY_TAG : value;
}

static void copy_status(const MPI_Status *status, int *fstatus) {
  int i;
  for (i = 0; i < HYP_STATUS_SIZE; i++) fstatus[i] = 0;
  fstatus[HYP_SOURCE] = status->MPI_SOURCE == MPI_ANY_SOURCE ? HYP_ANY_SOURCE :
                        status->MPI_SOURCE == MPI_PROC_NULL ? HYP_PROC_NULL :
                        status->MPI_SOURCE;
  fstatus[HYP_TAG] = status->MPI_TAG == MPI_ANY_TAG ? HYP_ANY_TAG : status->MPI_TAG;
  fstatus[HYP_ERROR] = status->MPI_ERROR;
}

/* Return a free slot in the request table, growing it if needed */
static int new_request(void) {
  int i, n_new;
  MPI_Request *tmp;
  for (i = 0; i < n_requests; i++)
    if (requests[i] == MPI_REQUEST_NULL) return i;
  n_new = n_requests == 0 ? 64 : 2 * n_requests;
  tmp = realloc(requests, n_new * sizeof(MPI_Request));
  if (tmp == NULL) fatal("could not allocate request table", n_new);
  requests = tmp;
  for (i = n_requests; i < n_new; i++) requests[i] = MPI_REQUEST_NULL;
  i = n_requests;
  n_requests = n_new;
  return i;
}

static MPI_Request *request(int handle) {
  if (handle < 1 || handle > n_requests) fatal("invalid request handle", handle);
  return &requests[handle - 1];
}

void hyp_mpi_init(int *integer_size, int *logical_size, int *real_size,
                  int *double_size, int *ierror) {
  default_integer = integer_type(*integer_size);
  default_logical = integer_type(*logical_size);
  default_real = real_type(*real_size);
  default_double = real_type(*double_size);
  *ierror = MPI_Init(NULL, NULL);
}

void hyp_mpi_finalize(int *ierror) {
  *ierror = MPI_Finalize();
}

void hyp_mpi_comm_rank(int *fcomm, int *rank, int *ierror) {
  *ierror = MPI_Comm_rank(comm(*fcomm), rank);
}

void hyp_mpi_comm_size(int *fcomm, int *size, int *ierror) {
  *ierror = MPI_Comm_size(comm(*fcomm), size);
}

void hyp_mpi_barrier(int *fcomm, int *ierror) {
  *ierror = MPI_Barrier(comm(*fcomm));
}

/* Copy the processor name into a blank-padded Fortran string of length
 * name_len, truncating it if needed */
void hyp_mpi_get_processor_name(char *name, int *name_len, int *resultlen,
                                int *ierror) {
  char buffer[MPI_MAX_PROCESSOR_NAME + 1];
  int length = 0;
  memset(buffer, 0, sizeof(buffer));
  *ierror = MPI_Get_processor_name(buffer, &length);
  if (length > *name_len) length = *name_len;
  if (length < 0) length = 0;
  memcpy(name, buffer, length);
  if (*name_len > length) memset(name + length, ' ', *name_len - length);
  *resultlen = length;
}

void hyp_mpi_bcast(void *buffer, int *count, int *ftype, int *root,
                   int *fcomm, int *ierror) {
  *ierror = MPI_Bcast(buffer, *count, datatype(*ftype), *root, comm(*fcomm));
}

void hyp_mpi_reduce(void *sendbuf, void *recvbuf, int *count, int *ftype,
                    int *fop, int *root, int *fcomm, int *ierror) {
  *ierror = MPI_Reduce(sendbuf, recvbuf, *count, datatype(*ftype), op(*fop),
                       *root, comm(*fcomm));
}

void hyp_mpi_allreduce(void *sendbuf, void *recvbuf, int *count, int *ftype,
                       int *fop, int *fcomm, int *ierror) {
  *ierror = MPI_Allreduce(sendbuf, recvbuf, *count, datatype(*ftype),
                          op(*fop), comm(*fcomm));
}

void hyp_mpi_send(void *buffer, int *count, int *ftype, int *dest, int *ftag,
                  int *fcomm, int *ierror) {
  *ierror = MPI_Send(buffer, *count, datatype(*ftype), source(*dest),
                     tag(*ftag), comm(*fcomm));
}

void hyp_mpi_recv(void *buffer, int *count, int *ftype, int *src, int *ftag,
                  int *fcomm, int *fstatus, int *ierror) {
  MPI_Status status;
  *ierror = MPI_Recv(buffer, *count, datatype(*ftype), source(*src),
                     tag(*ftag), comm(*fcomm), &status);
  copy_status(&status, fstatus);
}

void hyp_mpi_isend(void *buffer, int *count, int *ftype, int *dest, int *ftag,
                   int *fcomm, int *frequest, int *ierror) {
  int i = new_request();
  *ierror = MPI_Isend(buffer, *count, datatype(*ftype), source(*dest),
                      tag(*ftag), comm(*fcomm), &requests[i]);
  *frequest = requests[i] == MPI_REQUEST_NULL ? 0 : i + 1;
}

void hyp_mpi_irecv(void *buffer, int *count, int *ftype, int *src, int *ftag,
                   int *fcomm, int *frequest, int *ierror) {
  int i = new_request();
  *ierror = MPI_Irecv(buffer, *count, datatype(*ftype), source(*src),
                      tag(*ftag), comm(*fcomm), &requests[i]);
  *frequest = requests[i] == MPI_REQUEST_NULL ? 0 : i + 1;
}

/* As in MPI, testing a null request returns flag = 1 and an empty status.
 * Completed requests are released and reset to the null request (0). */
void hyp_mpi_test(int *frequest, int *flag, int *fstatus, int *ierror) {
  MPI_Status status;
  if (*frequest == 0) {
    *flag = 1;
    *ierror = MPI_SUCCESS;
    status.MPI_SOURCE = MPI_ANY_SOURCE;
    status.MPI_TAG = MPI_ANY_TAG;
    status.MPI_ERROR = MPI_SUCCESS;
  } else {
    *ierror = MPI_Test(request(*frequest), flag, &status);
    if (*flag) *frequest = 0;
  }
  if (*flag) copy_status(&status, fstatus);
}

void hyp_mpi_request_free(int *frequest, int *ierror) {
  *ierror = MPI_Request_free(request(*frequest));
  *frequest = 0;
}

/* The statuses are not returned to Fortran (the Fortran side only supports
 * mpi_statuses_ignore). They are still requested from MPI since passing
 * MPI_STATUSES_IGNORE triggers spurious -Wstringop-overflow warnings with
 * some combinations of GCC and MPICH. */
void hyp_mpi_waitall(int *count, int *frequests, int *ierror) {
  int i;
  MPI_Request *tmp;
  MPI_Status *statuses;
  if (*count <= 0) {
    *ierror = MPI_SUCCESS;
    return;
  }
  tmp = malloc(*count * sizeof(MPI_Request));
  statuses = malloc(*count * sizeof(MPI_Status));
  if (tmp == NULL || statuses == NULL)
    fatal("could not allocate requests for waitall", *count);
  for (i = 0; i < *count; i++)
    tmp[i] = frequests[i] == 0 ? MPI_REQUEST_NULL : *request(frequests[i]);
  *ierror = MPI_Waitall(*count, tmp, statuses);
  for (i = 0; i < *count; i++) {
    if (frequests[i] != 0) *request(frequests[i]) = tmp[i];
    if (tmp[i] == MPI_REQUEST_NULL) frequests[i] = 0;
  }
  free(statuses);
  free(tmp);
}
