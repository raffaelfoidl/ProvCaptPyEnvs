# important: process ids are global, i. e. are preserved (same pid for each instance) ==> <> os-managed pid
import json
from typing import Iterator, Sequence
import os
import locale
import sys
import argparse

root, filename = os.path.split(__file__)
proj_root = os.path.realpath(os.path.join(root, "..", ".."))
locale.setlocale(locale.LC_ALL, "de_AT.UTF-8")  # "" for auto, e. g. german: de_AT.UTF-8
sys.path.append(proj_root)

from instances.large.process_log import ProcessLog
from instances.large.persistence_helper import persist_summary, save_summary_plot, persist_conflict_report, save_plot
from instances.large.processing_helper import get_logs_by_id, get_runtime, get_overlaps, get_conflicts, \
    get_concurrent_accesses_per_resource, get_conflicts_per_resource, get_resource_summary


def parse_args():
    parser = argparse.ArgumentParser(description="Reads process traces from json files and analyzes them with respect "
                                                 "to possible sources of resource conflicts. A plot describing the"
                                                 " number of traces per PID and one showing the number of resource "
                                                 "accesses (read, write) as well as possible conflicts are saved. "
                                                 "The underlying data for the plots will be persisted as csv and JSON.")
    parser.add_argument("pid", metavar="pid", type=int, help="ID of the process to analyze")
    parser.add_argument("freqs", metavar="freqs", type=str, help="path frequency plot should be persisted to")
    parser.add_argument("summary_csv", metavar="summary_csv", type=str,
                        help="path resource summary (csv) should be persisted to")
    parser.add_argument("summary_plot", metavar="summary_plot", type=str,
                        help="path resource summary (plot) should be persisted to")
    parser.add_argument("conflicts", metavar="conflicts", type=str, help="path conflict report should be persisted to")
    parser.add_argument("traces", metavar="traces", nargs="+", type=str, help="process trace logs (JSON) to analyze")
    return parser.parse_args()


def load_data(paths: Sequence[str]) -> Sequence[ProcessLog]:
    return_value = []
    for path in paths:
        with open(path) as file:
            data_lst = json.load(file)
            return_value.extend(map(ProcessLog.deserialize, data_lst))

    return return_value


# count of entries, unique pids, all pids (for histogram)
def get_pids(data: Sequence[ProcessLog]) -> (int, Sequence[int], Sequence[int]):
    seen = set()
    count = 0
    pids = []
    for obj in data:
        count += 1
        pids.append(obj.pid)
        if obj.pid not in seen:
            seen.add(obj.pid)

    return count, seen, pids

"""
@begin inst_l.main
@param pid @desc ID of process to analyze
@param freqs @desc persistence path for frequency plot
@param summary_csv @desc persistence path for csv summary
@param summary_plot @desc persistence path for plot summary
@param conflicts @desc persistence path for conflict report
@in traces @desc paths of process trace logs to analyze

@out frequency_plot @uri file:{freqs}
@out conflict_report @uri file:{conflicts}
@out res_summary_csv @uri file:{summary_csv}
@out res_summary_plot @uri file:{summary_plot}
"""


def main():
    args = parse_args()

    """
    @begin load_data @desc read process trace logs
    @in traces
    @out data
    """
    print("Loading data...")
    data = load_data(args.traces)
    print("Done.\n")
    """
    @end load_data
    """

    """
    @begin get_pids @desc determine PIDs stored\nin trace logs
    @in data
    @out count
    @out distinct_pids
    @out all_pids
    """
    print("Initial analysis...")
    count, distinct_pids, all_pids = get_pids(data)
    """
    @end get_pids
    """

    """
    @begin provide_data_info @desc print count and names of\nprocesses; save frequency plot
    @in count
    @in distinct_pids
    @in all_pids
    @in freqs
    
    @out frequency_plot @uri file:{freqs}
    """
    print("Done. Read {0:n} process log entries from {1} files.\n".format(count, len(args.traces)))
    print("The following {0} processes were captured in the log:".format(len(distinct_pids)))
    print(sorted(distinct_pids))
    save_plot(all_pids, args.freqs)
    print("(See plot {0} for frequency distribution.)".format(os.path.basename(args.freqs)))
    """
    @end provide_data_info
    """

    print("\u2500" * 75)  # unicode character "box drawings light horizontal"
    print("Start gathering information about process with ID {0}...".format(args.pid))
    if args.pid not in distinct_pids:
        print("\nError! PID must be part of the list above (process must be captured in input traces). Abort.")
        exit(1)

    """
    @begin get_logs @desc retrieve trace logs\nof specified process
    
    @in data
    @in pid
    
    @out pid_logs
    """
    pid_logs = get_logs_by_id(data, args.pid)  # there are len(pid_logs) instances recorded of that process
    """
    @end get_logs
    """

    """
    @begin get_process_runtime @desc compute total and average runtime
    
    @in pid_logs
    @out total_runtime
    @out avg_runtime
    """
    total_runtime = get_runtime(pid_logs)
    avg_runtime = total_runtime // len(pid_logs)
    """
    @end get_process_runtime
    """

    """
    @begin get_overlaps @desc determine overlapping\nPID trace logs
    
    @in pid_logs
    @out concurrent_executions
    @out overall_resource_accesses
    """
    concurrent_executions, overall_resource_accesses = get_overlaps(pid_logs)
    """
    @end get_overlaps
    """

    """
    @begin get_conflicts @desc determine write-write conflicts
    
    @in concurrent_executions
    @out res_conflicts
    """
    conflicts = get_conflicts(concurrent_executions)
    """
    @end get_conflicts
    """

    """
    @begin get_resource_info @desc determine usage and\nresource conflict infos
    
    @in concurrent_executions
    @in conflicts
    @out concurrent_accesses_per_resource
    @out conflicts_per_resource
    """
    concurrent_accesses_per_resource = get_concurrent_accesses_per_resource(concurrent_executions)
    conflicts_per_resource = get_conflicts_per_resource(conflicts)
    """
    @end get_resource_info
    """

    """
    @begin get_resource_summary @desc get dict representation\nof resource summary
    
    @in concurrent_accesses_per_resource
    @in conflicts_per_resource
    @out resource_summary
    """
    resource_summary = get_resource_summary(concurrent_accesses_per_resource, conflicts_per_resource)
    print("Done.\n")
    """
    @end get_resource_summary
    """

    print("Persisting plot and summaries...")

    """
    @begin persist_res_summary @desc save resource summary\nas CSV file and plot
    
    @in resource_summary
    @in summary_csv
    @in summary_plot
    @in pid
    
    @out res_summary_csv @uri file:{summary_csv}
    @out res_summary_plot @uri file:{summary_plot}
    """
    persist_summary(resource_summary, args.summary_csv.replace(".csv", "_{0}.csv".format(args.pid)))
    save_summary_plot(resource_summary, args.summary_plot.replace(".jpg", "_{0}.jpg".format(args.pid)), args.pid)
    """
    @end persist_resource_summary
    """

    """
    @begin persist_conflict_report @desc save conflict report\nas JSON file
    
    @in res_conflicts
    @in total_runtime
    @in avg_runtime
    @in pid
    @in conflicts
    
    @out conflict_report @uri file:{conflicts}
    """
    persist_conflict_report(conflicts, total_runtime, avg_runtime, args.pid,
                            args.conflicts.replace(".json", "_{0}.json".format(args.pid)))
    print("Done.")
    """
    @end persist_conflict_report
    """


"""
@end inst_l.main
"""

if __name__ == "__main__":
    main()
