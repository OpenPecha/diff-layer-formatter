from email import charset
import json
from pathlib import Path

from openpecha.utils import dump_yaml,load_yaml

from diff_layer_parser import get_diff_layer
from diff_selector import get_combined_diff_layer, get_alt_diff_paths, reformat_combined_diff_layer
from get_diff_layer import get_annotated_diffs

def save_editons_with_diffs(text_id, open_edition_text_path, alt_edition_text_paths):
    open_edition_text = open_edition_text_path.read_text(encoding="utf-8")
    alt_edition_text_paths.sort()
    for alt_edition_text_path in alt_edition_text_paths:
        alt_edition_text = alt_edition_text_path.read_text(encoding='utf-8')
        edition_with_diffs = get_annotated_diffs(open_edition_text, alt_edition_text)
        Path(f'./data/{text_id}/editions_with_diff/OE_{alt_edition_text_path.stem}.txt').write_text(edition_with_diffs, encoding='utf-8')
    
def save_diff_layers(text_id):
    edition_with_diff_paths = list(Path(f'./data/{text_id}/editions_with_diff').iterdir())
    for edition_with_diff_path in edition_with_diff_paths:
        edition_with_diff = edition_with_diff_path.read_text(encoding='utf-8')
        diff_layer = get_diff_layer(edition_with_diff)
        layer_fn = Path(f'./data/{text_id}/diff_layers/Diff_{edition_with_diff_path.stem}.yml')
        dump_yaml(json.loads(diff_layer.json()), layer_fn)

def save_combined_diff_layer(text_id):
    combined_diffs = {}
    diff_layer_paths = list(Path(f'./data/{text_id}/diff_layers').iterdir())
    number_of_editions = len(diff_layer_paths)+1
    for diff_layer_path in diff_layer_paths:
        alt_diff_layer_paths = get_alt_diff_paths(diff_layer_path, diff_layer_paths)
        combined_diffs = get_combined_diff_layer(diff_layer_path, alt_diff_layer_paths, combined_diffs, number_of_editions=number_of_editions)
    combined_diffs = reformat_combined_diff_layer(combined_diffs)
    dump_yaml(combined_diffs, Path(f'./data/{text_id}/combined_diff.yml'))
    return combined_diffs

def is_sub_set_of_prev(diff, prev_diff):
    if diff != prev_diff and diff['span']['start'] < prev_diff['span']['end']:
        return True
    return False

def serialize_diffs(combined_diff_layer, open_edition):
    new_open_edition = ""
    char_walker = 0
    prev_diff = list(combined_diff_layer.values())[0]
    for _, diff in combined_diff_layer.items():
        if is_sub_set_of_prev(diff, prev_diff):
            continue
        diff_start = diff['span']['start']
        diff_end = diff['span']['end']
        elected_diff = diff['elected']
        new_open_edition += f"{open_edition[char_walker:diff_start]}{elected_diff}"
        char_walker = diff_end
        prev_diff = diff
    new_open_edition += open_edition[char_walker:]
    return new_open_edition



def pipeline(text_id):
    alt_edition_text_paths = list(Path(f'./data/{text_id}/editions').iterdir())
    open_edition_text_path = Path(f'./data/{text_id}/OE.txt')
    save_editons_with_diffs(text_id, open_edition_text_path, alt_edition_text_paths)
    print("INFO: Edition with diffs completed..")
    save_diff_layers(text_id)
    print("INFO: Diff layers saved..")
    combined_diff_layers = save_combined_diff_layer(text_id)
    print("INFO: Combined diff layer generated..")
    new_open_editions = serialize_diffs(combined_diff_layers, open_edition_text_path.read_text(encoding='utf-8'))
    Path(f'./data/{text_id}/new_OE.txt').write_text(new_open_editions, encoding='utf-8')

    
if __name__ == "__main__":
    text_id = "D3871"
    pipeline(text_id)