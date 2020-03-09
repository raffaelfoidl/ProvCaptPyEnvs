from datetime import datetime
from enum import Enum
from typing import Sequence

import dateutil.parser


class FileMode(Enum):
    READ = "r"
    WRITE = "w"
    NONE = "n"


class ProcessLog:

    def __init__(self, pid: int = None, start: datetime = None, end: datetime = None, resources: Sequence[str] = None,
                 mode: FileMode = None):
        self.pid = pid
        self.start = start
        self.end = end
        self.resources = resources
        self.mode = mode

    @staticmethod
    def deserialize(json: dict) -> "ProcessLog":
        start = dateutil.parser.parse(json["start"])
        end = dateutil.parser.parse(json["end"])
        return ProcessLog(json["pid"], start, end, json["resources"], FileMode(json["mode"]))

    def serialize(self, include_pid_res: bool = False) -> dict:
        ret_dict = {"pid": self.pid, "start": self.start.isoformat(), "end": self.end.isoformat(),
                    "resources": self.resources, "mode": self.mode.value}
        if not include_pid_res:
            del ret_dict["resources"]
            del ret_dict["pid"]

        return ret_dict

    def __repr__(self):
        return "PID {0} from {1} to {2}; resources [{3}]; mode {4}" \
            .format(self.pid, self.start, self.end, ", ".join(self.resources), self.mode)

    def __str__(self):
        return "[PID {0}]".format(self.pid)
