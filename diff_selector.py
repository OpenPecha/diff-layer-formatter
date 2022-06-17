from collections import OrderedDict
from operator import getitem
from pathlib import Path


from openpecha.utils import load_yaml, dump_yaml


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

def add_missing_diff(diffs, cur_diff, number_of_editions):
    if len(diffs) == number_of_editions-1:
        diffs.append(cur_diff['src_diff'])
    else:
        for i in range(0, number_of_editions-len(diffs)):
            diffs.append(cur_diff['src_diff'])
    return diffs

def get_elected_diff(diffs, cur_diff, number_of_editions):
    diff_n_count = {}
    unique_diffs = list(set(diffs))
    for unique_diff in unique_diffs:
        diff_n_count[unique_diff] = diffs.count(unique_diff)
    for diff, count in diff_n_count.items():
        if count > number_of_editions/2:
            return diff
    return cur_diff['src_diff']


def get_combined_diff_layer(cur_diff_path, alt_diff_layer_paths, combined_diffs, number_of_editions):
    cur_diff_layer = load_yaml(cur_diff_path)
    for uuid, cur_diff in cur_diff_layer['annotations'].items():
        if diffs := has_alt_diffs(cur_diff, alt_diff_layer_paths):
            if cur_diff['span']['start'] not in combined_diffs:
                diffs.append(cur_diff['diff_payload'])
                diffs = add_missing_diff(diffs, cur_diff, number_of_editions)
                elected_diff = get_elected_diff(diffs, cur_diff, number_of_editions)
                combined_diffs[cur_diff['span']['start']] = {
                    'diffs': diffs,
                    'elected': elected_diff,
                    'span': cur_diff['span'],
                    'id': cur_diff['id']
                }
    return combined_diffs

def reformat_combined_diff_layer(combined_diffs):
    reformated_combined_diff_layer = {}
    for _, diff in combined_diffs.items():
        reformated_combined_diff_layer[diff['id']] = {
            'span': diff['span'],
            'diffs': diff['diffs'],
            'elected': diff['elected'],
            'start': diff['span']['start']
        }
    sorted_reformated_combined_diff_layer = OrderedDict(sorted(reformated_combined_diff_layer.items(),
       key = lambda x: getitem(x[1], 'start')))
    sorted_reformated_combined_diff_layer = dict(sorted_reformated_combined_diff_layer)
    for id, diff in sorted_reformated_combined_diff_layer.items():
        sorted_reformated_combined_diff_layer[id] = {
            'span': diff['span'],
            'diffs': diff['diffs'],
            'elected': diff['elected'],
        }
    return sorted_reformated_combined_diff_layer

def get_alt_diff_paths(cur_diff_path, diff_paths):
    alt_diff_paths = []
    for diff_path in diff_paths:
        if diff_path == cur_diff_path:
            continue
        alt_diff_paths.append(diff_path)
    return alt_diff_paths


if __name__ == "__main__":
    combined_diffs = {}
    diff_layer_paths = [
        Path("./data/D3871/diff_layers/Diff_OE_E1.yml"),
        Path("./data/D3871/diff_layers/Diff_OE_E2.yml"), 
        Path("./data/D3871/diff_layers/Diff_OE_E3.yml"),
        Path('./data/D3871/diff_layers/Diff_OE_E4.yml')
        ]
    for diff_layer_path in diff_layer_paths:
        alt_diff_layer_paths = get_alt_diff_paths(diff_layer_path, diff_layer_paths)
        combined_diffs = get_combined_diff_layer(diff_layer_path, alt_diff_layer_paths, combined_diffs, number_of_editions=5)
        combined_diffs = reformat_combined_diff_layer(combined_diffs)
    dump_yaml(combined_diffs, Path('./combined_diff.yml'))





