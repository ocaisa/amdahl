import time
import sys
import argparse

from mpi4py import MPI

"""
Gather timing data in order to plot speedup *S* vs. number of cores *N*,
which should follow Amdahl's Law:

           1
    S = -------
        s + p/N

where *s* is the serial proportion of the total work and *p* the
parallelizable proportion.
"""

def do_work(work_time=30, parallel_proportion=0.8, comm=MPI.COMM_WORLD):
    # How many MPI ranks (cores) are we?
    size = comm.Get_size()
    # Who am I in that set of ranks?
    rank = comm.Get_rank()
    # Where am I running?
    name = MPI.Get_processor_name()

    if rank == 0:
        # Set the sleep times (which are used to fake the amount of work)
        serial_sleep_time = float(work_time) * (1.0 - parallel_proportion)
        parallel_sleep_time = (float(work_time) * parallel_proportion) / size

        # Use Amdahl's law to calculate the expected speedup for this workload
        amdahl_speed_up = 1.0 / (
            (1.0 - parallel_proportion) + parallel_proportion / size
        )

        suffix = "" if size == 1 else "s"

        sys.stdout.write(
            "Doing %f seconds of 'work' on %s processor%s,\n"
            " which should take %f seconds with %f parallel"
            " proportion of the workload.\n\n"
            % (
                work_time,
                size,
                suffix,
                work_time / amdahl_speed_up,
                parallel_proportion,
            )
        )

        sys.stdout.write(
            "  Hello, World! I am process %d of %d on %s."
            " I will do all the serial 'work' for"
            " %f seconds.\n" % (rank, size, name, serial_sleep_time)
        )
        time.sleep(serial_sleep_time)
    else:
        parallel_sleep_time = None

    # Tell all processes how much work they need to do using 'bcast' to broadcast
    # (this also creates an implicit barrier, blocking processes until they receive
    # the value)
    parallel_sleep_time = comm.bcast(parallel_sleep_time, root=0)

    # This is where everyone pretends to do work (while really we are just sleeping)
    sys.stdout.write(
        "  Hello, World! I am process %d of %d on %s. I will do parallel 'work' for "
        "%f seconds.\n" % (rank, size, name, parallel_sleep_time)
    )
    time.sleep(parallel_sleep_time)


def parse_command_line():
    # Initialize our argument parser
    parser = argparse.ArgumentParser()
    # Adding optional arguments
    parser.add_argument(
        "-p",
        "--parallel-proportion",
        nargs="?",
        const=0.8,
        type=float,
        default=0.8,
        help="Parallel proportion should be a float between 0 and 1",
    )
    parser.add_argument(
        "-w",
        "--work-seconds",
        nargs="?",
        const=30,
        type=int,
        default=30,
        help="Total seconds of workload, should be an integer greater than 0",
    )
    # Read arguments from command line
    args = parser.parse_args()
    if not args.work_seconds > 0:
        parser.print_help()
        MPI.COMM_WORLD.Abort(1)
        sys.exit(1)
    if args.parallel_proportion <= 0 or args.parallel_proportion > 1:
        parser.print_help()
        MPI.COMM_WORLD.Abort(1)
        sys.exit(1)

    return args


def amdahl():
    """Amdahl's law illustrator (with fake work)"""
    rank = MPI.COMM_WORLD.Get_rank()
    # Only the root process handles the command line arguments
    if rank == 0:
        # Start a clock to measure total time
        start = time.time()

        args = parse_command_line()

        do_work(
            work_time=args.work_seconds, parallel_proportion=args.parallel_proportion
        )
        end = time.time()
        sys.stdout.write(
            "\nTotal execution time (according to rank 0): %f seconds\n" % (end - start)
        )
    else:
        do_work()
