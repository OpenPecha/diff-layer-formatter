import re
import json

from openpecha.core.layer import Layer, LayerEnum
from openpecha.core.annotations import Diff, Span
from openpecha.utils import dump_yaml

from pathlib import Path

def get_chunks(oe_with_diffs):
    chunks = []
    cur_chunk = ""
    text_parts = re.split("(\[.+?,.+?\])", oe_with_diffs)
    for text_part in text_parts:
        if re.search("\[.+?,.+?\]", text_part):
            cur_chunk += text_part
            chunks.append(cur_chunk)
            cur_chunk = ""
        else:
            cur_chunk += text_part
    return chunks

def parse_diff_anns(chunk, char_walker):
    diff_ann = re.search("\[(.+?),(.+?)\]", chunk)
    src_txt = diff_ann.group(1)
    diff_payload = diff_ann.group(2)
    ann_start = diff_ann.start() + char_walker
    ann_end = ann_start + len(src_txt)
    span = Span(start=ann_start, end=ann_end)
    diff_ann = Diff(span=span, src_diff=src_txt, diff_payload=diff_payload)
    return diff_ann





def get_diff_layer(oe_with_diffs):
    char_walker = 0
    diff_layer = Layer(annotation_type=LayerEnum.diff)
    
    oe_with_diffs = oe_with_diffs.replace("\n","#")
    chunks = get_chunks(oe_with_diffs)
    for chunk in chunks:
        diff_layer.set_annotation(parse_diff_anns(chunk, char_walker))
        chunk_without_ann = re.sub("\[(.+?),.+?\]", "\g<1>", chunk)
        char_walker += len(chunk_without_ann)
    return diff_layer  


if __name__ == "__main__":
    oe_with_diffs = Path('./OE_E4.txt').read_text(encoding='utf-8')
    diff_layer = get_diff_layer(oe_with_diffs)
    layer_fn = Path('./Diff_E4.yml')
    dump_yaml(json.loads(diff_layer.json()), layer_fn)   
