import collections
import itertools
import os
import json
import csv
import locale
from typing import List, NamedTuple, Tuple, Iterator, Any
import argparse
import PIL
from collections import OrderedDict

root, filename = os.path.split(__file__)
by_country_path = os.path.join(root, "by_country.json")
overall_path = os.path.join(root, "overall.json")
Entry = NamedTuple("Entry")  # type: NamedTuple
locale.setlocale(locale.LC_ALL, "de_AT.UTF-8")  # "" for auto, e. g. german: de_AT.UTF-8


def parse_args():
    parser = argparse.ArgumentParser(description="Processes a list of wind speed measurements. "
                                                 "Persists two top ten lists (JSON): overall max per city, average "
                                                 "max by country. Both summaries include a wind "
                                                 "speed classification according to the Beaufort scale for each entry.")
    parser.add_argument("data", metavar="data", type=str,
                        help="input file path (csv with country, code, city, wind_speed)")
    return parser.parse_args()


def read_file(path: str) -> List[Entry]:
    """Read the CSV input data as NamedTuple"""
    global Entry
    with open(path) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=",")
        headers_processed = False
        return_value = []

        for row in csv_reader:
            if not headers_processed:
                Entry = collections.namedtuple("Entry", row)
                headers_processed = True
            else:
                return_value.append(Entry(*row))

    return return_value


def get_classification(speed: float) -> Tuple[float, str]:
    infinity = float("inf")
    classes = OrderedDict([
        ((0, 0.), "Calm"),
        ((1, 1.85), "Light Airs"),
        ((2, 7.41), "Light breeze"),
        ((3, 12.96), "Gentle breeze"),
        ((4, 20.37), "Moderate breeze"),
        ((5, 29.63), "Fresh breeze"),
        ((6, 40.74), "Strong breeze"),
        ((7, 51.86), "Moderate (near) gale"),
        ((8, 62.97), "Fresh gale"),
        ((9, 75.93), "Strong or severe gale"),
        ((10, 88.9), "Whole gale or Storm"),
        ((11, 103.71), "Violent Storm"),
        ((12, 118.53), "Hurricane"),
        ((12, infinity), "Hurricane")
    ])

    items = list(classes.keys())
    for i, (level, lower) in enumerate(items[:-1]):
        _, lower_next = items[i + 1]
        if lower < speed <= lower_next:
            return level, classes[(level, lower)]
    return -1, "unknown"


def get_top_ten_by_country(data: Iterator[Tuple[Any, Iterator]]) -> List[Tuple[float, List[Entry]]]:
    ret_lst = []
    for key, group in data:
        entries = list(group)
        sum_speed = sum(float(item.wind_speed) for item in entries)
        avg_speed = sum_speed / len(entries)
        ret_lst.append((avg_speed, entries))

    ret_lst.sort(key=lambda item: item[0], reverse=True)  # sort by avg speed
    return ret_lst[:10]  # return first 10 elements


def persist_top_ten_by_country(data: List[Tuple[float, List[Entry]]], path: str):
    dict_to_persist = []

    for i, (speed, lst) in enumerate(data):
        level, description = get_classification(float(speed))
        entries_repr = [{"city": x.city, "speed": x.wind_speed} for x in lst]
        dict_to_persist.append(
            {"rank": i + 1, "avg_wind_speed": speed, "country": lst[0].country, "country_code": lst[0].code,
             "entries": entries_repr, "classification": "{0} (level {1})".format(description, level)})

    with open(path, "w") as file:
        json.dump(dict_to_persist, file, indent=2)


def get_top_ten_overall(data: Iterator[Tuple[Any, Iterator]]) -> List[Entry]:
    return sorted(data, key=lambda item: float(item.wind_speed), reverse=True)[:10]


def persist_top_ten_overall(data: List[Entry], path: str):
    dict_to_persist = []

    for i, (country, code, city, wind_speed) in enumerate(data):
        level, description = get_classification(float(wind_speed))
        dict_to_persist.append(
            {"rank": i + 1, "wind_speed": wind_speed, "country": country, "country_code": code, "city": city,
             "classification": "{0} (level {1})".format(description, level)})

    with open(path, "w") as file:
        json.dump(dict_to_persist, file, indent=2)


"""
@begin inst_s.main @desc Processes a list of wind speed measurements

@in data @desc CSV file with country, code, city, wind_speed as columns
@out summary_by_country @uri file:by_country.json
@out summary_overall @uri file:overall.json
"""


def main():
    args = parse_args()
    print("Reading data...")

    if not os.path.exists(args.data):
        print("Could not find data file. Abort.")
        exit(1)

    """
    @begin read_file @desc read CSV data as NamedTuple
    @in data
    @out data_parsed @desc CSV data as NamedTuple
    """
    data = read_file(args.data)  # type: List[Entry]
    data.sort(key=lambda x: x.country)  # sort by country (for groupby)
    print("Done.\n")
    """
    @end read_file
    """

    if len(data) < 1:
        print("No entries found.")
        exit(0)

    print("Processing...")

    """
    @begin group_data_by_country @desc split data by country
    @param data_parsed
    @out data_by_country @desc [output] contries grouped by country (list of sublists)
    """
    data_by_country = itertools.groupby(data, key=lambda x: x.country)
    """
    @end group_data_by_country
    """

    """
    @begin get_top_ten_by_country @desc 10 countries with highest\navg wind speed
    @param data_by_country @desc [input] country-grouped data
    @out country_top_ten
    """
    top_ten_by_country = get_top_ten_by_country(data_by_country)
    """
    @end get_top_ten_by_country
    """

    """
    @begin get_top_ten_overall @desc sort by wind speed,\nreturn first 10 items
    @param data_parsed
    @out overall_top_ten
    """
    top_ten_overall = get_top_ten_overall(data)
    """
    @end get_top_ten_overall
    """

    print("Done.\n")

    print("Saving summaries to {0} and {1}..."
          .format(os.path.basename(by_country_path), os.path.basename(overall_path)))

    """
    @begin persist_top_ten_by_country
    @in country_top_ten
    @out summary_by_country @uri file:by_country.json
    @call get_classification @desc maps wind speed to Beaufort scale
    """
    persist_top_ten_by_country(top_ten_by_country, by_country_path)
    """
    @end persist_top_ten_by_country
    """

    """
    @begin persist_top_ten_overall
    @param overall_top_ten
    @out summary_overall @uri file:overall.json
    @call get_classification
    """
    persist_top_ten_overall(top_ten_overall, overall_path)
    """
    @end persist_top_ten_overall
    """
    print("Done.")


"""
@end inst_s.main
"""

if __name__ == "__main__":
    main()
