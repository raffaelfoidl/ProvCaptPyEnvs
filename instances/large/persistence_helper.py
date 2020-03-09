import collections
import csv
import json
from datetime import timedelta
from typing import Dict, Tuple, Sequence

import numpy as np
from matplotlib import pyplot as plt

from instances.large.process_log import ProcessLog


def persist_summary(summary: Dict[str, Tuple[int, int, int]], path: str):
    headers = ["resource", "read", "write", "conflicts"]

    with open(path, "w") as file:
        csv_writer = csv.writer(file)
        csv_writer.writerow(headers)

        for k, v in sorted(summary.items()):
            csv_writer.writerow([k] + list(v))


def put_label(ax, rects):
    # turn off both (major + minor) ticks of x axis
    ax.tick_params(axis="x", which="both", bottom=False, top=False, labelbottom=False)

    for rect in rects:
        height = rect.get_height()
        ax.annotate("{}".format(height), xy=(rect.get_x() + rect.get_width() / 2, height), xytext=(0, 3),
                    textcoords="offset points", ha="center", va="bottom")


def save_summary_plot(data: Dict[str, Tuple[int, int, int]], path: str, pid):
    fig = plt.figure(figsize=(12, 10))
    ax = None

    for i, (k, (r, w, c)) in enumerate(sorted(data.items())):
        ax = fig.add_subplot(5, 6, i + 1)
        x = np.arange(1)  # label locations
        width = 0.35  # bar widths

        rects1 = ax.bar(x - width * 1.1, r, width, label="Read Accesses")
        rects2 = ax.bar(x, w, width, label="Write Accesses")
        rects3 = ax.bar(x + width * 1.1, c, width, label="Possible Conflicts")
        ax.set_xlabel("Resource {0}".format(k))

        put_label(ax, rects1)
        put_label(ax, rects2)
        put_label(ax, rects3)

    handles, labels = ax.get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower right", prop={"size": 20})

    plt.suptitle("Resource Usage Summary (PID {0})".format(pid), fontsize=20)
    fig.tight_layout(rect=[0, 0.04, 1, 0.96])  # make plot rect smaller to make space for title
    fig.savefig(path)


def persist_conflict_report(conflicts: Sequence[Tuple[ProcessLog, ProcessLog, Sequence[str]]], total_runtime: timedelta,
                            avg_runtime: timedelta, pid: int, path: str):
    dict_to_persist = {"pid": pid, "runtime_total": str(total_runtime), "runtime_avg": str(avg_runtime),
                       "potential_conflicts": []}
    for x, y, resources in conflicts:
        dict_to_persist["potential_conflicts"].append(
            {"log1": x.serialize(), "log2": y.serialize(), "affected_resources": resources})

    with open(path, "w") as file:
        json.dump(dict_to_persist, file, indent=2)


def save_plot(pids_freqs: Sequence[int], path):
    fig, ax = plt.subplots()

    counter = collections.Counter(pids_freqs)
    x, y = [], []

    # sort by x values (PIDs)
    for k, v in sorted(counter.items(), key=lambda item: item[0]):
        x.append(k)
        y.append(v)

    ax.plot(y, marker="o")
    ax.set_xticks([i for i in range(len(y))])
    ax.set_xticklabels(x)
    ax.set_xlabel("PID")
    ax.set_ylabel("Number of Log Entries")
    plt.savefig(path)
