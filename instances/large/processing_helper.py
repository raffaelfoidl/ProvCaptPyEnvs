import itertools
from datetime import timedelta, datetime
from typing import Sequence, Tuple, Dict

from instances.large.process_log import ProcessLog, FileMode


def get_logs_by_id(logs: Sequence[ProcessLog], pid: int) -> Sequence[ProcessLog]:
    return [log for log in logs if log.pid == pid]


def get_runtime(logs: Sequence[ProcessLog]) -> timedelta:
    runtime = timedelta(0)
    for log in logs:
        runtime += log.end - log.start

    return runtime


def get_overlaps(logs: Sequence[ProcessLog]) -> Tuple[Sequence[Tuple[ProcessLog, ProcessLog]], int]:
    combinations = itertools.combinations(logs, 2)
    overlaps = []
    resource_accesses = 0

    for x, y in combinations:
        resource_accesses += len(x.resources) + len(y.resources)
        if dates_overlap(x.start, x.end, y.start, y.end):
            overlaps.append((x, y))

    return overlaps, resource_accesses


def dates_overlap(start1: datetime, end1: datetime, start2: datetime, end2: datetime):
    return start1 <= end2 and end1 >= start2


def get_conflicts(overlaps: Sequence[Tuple[ProcessLog, ProcessLog]]) -> \
        Sequence[Tuple[ProcessLog, ProcessLog, Sequence[str]]]:
    conflicting_tuples = []
    for x, y, in overlaps:
        intersection = list(set(x.resources).intersection(y.resources))
        # intersection not empty and mode conflict
        if intersection and x.mode == FileMode.WRITE and y.mode == FileMode.WRITE:
            conflicting_tuples.append((x, y, intersection))

    return conflicting_tuples


# returns dict with resource name as key and (read-accesses, write-accesses)-tuple as value
def get_concurrent_accesses_per_resource(concurrent_execs: Sequence[Tuple[ProcessLog, ProcessLog]]) -> \
        Dict[str, Tuple[int, int]]:
    # unique list of executions (equals flattened list of concurrent ProcessLogs without duplicates)
    execs = set([item for t in concurrent_execs for item in t])
    ret_dict = {}

    for execution in execs:
        for res in execution.resources:
            if res not in ret_dict:
                ret_dict[res] = (0, 0)

            current_r, current_w = ret_dict[res]
            if execution.mode == FileMode.READ:
                ret_dict[res] = (current_r + 1, current_w)
            elif execution.mode == FileMode.WRITE:
                ret_dict[res] = (current_r, current_w + 1)

    return ret_dict


# returns dict with resource name as key and number of conflicts as value
def get_conflicts_per_resource(conflicts: Sequence[Tuple[ProcessLog, ProcessLog, Sequence[str]]]) -> Dict[str, int]:
    ret_dict = {}

    for x, y, resources in conflicts:
        for res in resources:
            if res not in ret_dict:
                ret_dict[res] = 0

            ret_dict[res] += 1

    return ret_dict


def get_resource_summary(accesses: Dict[str, Tuple[int, int]], conflicts: Dict[str, int]) -> \
        Dict[str, Tuple[int, int, int]]:
    # dict comprehension: take values of access and add a third component to the tuple by adding (conflicts[k], )
    # (= access int in conflicts dict with key k) -> if key does not exist, take 0 (= no conflicts for this resource)
    return {k: (v + (conflicts.get(k, 0),)) for k, v in accesses.items()}
