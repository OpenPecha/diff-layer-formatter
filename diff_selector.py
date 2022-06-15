
from openpecha.utils import load_yaml, dump_yaml

from pathlib import Path

def find_alt_diff(diff_start, alt_diff_layer):
    for uuid, diff in alt_diff_layer['annotations'].items():
        if diff['span']['start'] == diff_start:
            return diff['diff_payload']
    return ""

def has_alt_diffs(diff, alt_diff_layer_paths):
    diff_start = diff['span']['start']
    alt_diffs = []
    for alt_diff_layer_path in alt_diff_layer_paths:
        alt_diff_layer = load_yaml(alt_diff_layer_path)
        if alt_diff := find_alt_diff(diff_start, alt_diff_layer):
            if alt_diff:
                alt_diffs.append(alt_diff)
    return alt_diffs


def get_combined_diff_layer(cur_diff_path, alt_diff_layer_paths, combined_diffs):
    cur_diff_layer = load_yaml(cur_diff_path)
    for uuid, diff in cur_diff_layer['annotations'].items():
        if alt_diffs := has_alt_diffs(diff, alt_diff_layer_paths):
            if alt_diffs and diff['span']['start'] not in combined_diffs:
                alt_diffs.append(diff['diff_payload'])
                combined_diffs[diff['span']['start']] = {
                    'alt_diffs': alt_diffs,
                    'src_txt': diff['src_diff'],
                }
    return combined_diffs

def get_alt_diff_paths(cur_diff_path, diff_paths):
    alt_diff_paths = []
    for diff_path in diff_paths:
        if diff_path == cur_diff_path:
            continue
        alt_diff_paths.append(diff_path)
    return alt_diff_paths


if __name__ == "__main__":
    combined_diffs = {}
    diff_layer_paths = ["./Diff_E1.yml", "./Diff_E2.yml", "./Diff_E3.yml", './Diff_E4.yml']
    for diff_layer_path in diff_layer_paths:
        alt_diff_layer_paths = get_alt_diff_paths(diff_layer_path, diff_layer_paths)
        combined_diffs = get_combined_diff_layer(diff_layer_path, alt_diff_layer_paths, combined_diffs)
    dump_yaml(combined_diffs, Path('./combined_diff.yml'))





