import re
import requests
import diff_match_patch as dmp_module

from antx.core import get_diffs, transfer
from pathlib import Path

# def get_diffs(textA, textB):
#     diff_response = requests.post(url='https://openpecha.bdrc.io/api/v1/diff/', json={"textA": textA, "textB": textB})
#     diffs = diff_response.json()
#     return diffs

def normalise_text(text):
    text = text.replace("\n", "")
    return text

def get_syls(text):
    chunks = re.split('(་|།།|།)',text)
    syls = []
    cur_syl = ''
    for chunk in chunks:
        if re.search('་|།།|།',chunk):
            cur_syl += chunk
            syls.append(cur_syl)
            cur_syl = ''
        else:
            cur_syl += chunk
    if cur_syl:
        syls.append(cur_syl)
    return syls

def is_punct_diffs(diff_text):
    punct_diffs = ["[་,༌]", "[་,། ]", '[།,    ]']
    for punct_diff in punct_diffs:
        if diff_text == punct_diff:
            return True
    return False

def reformat_diff_text_from_right(diff_text, right_diff_text, second_right_diff, diffs, diff_walker):
    reformated_diff_text = f"[{diff_text},{right_diff_text}]"
    if is_punct_diffs(reformated_diff_text):
        return diff_text,diffs
    sr_diff_type, sr_diff_text = second_right_diff
    if second_right_diff == [0, ""]:
        return reformated_diff_text, diffs
    if sr_diff_type == 0:
        if sr_diff_text[0] == "་":
            reformated_diff_text = f"[{diff_text}་,{right_diff_text}་]"
            diffs[diff_walker+2][1] = sr_diff_text[1:]
        elif diff_text[-1] != "་" or diff_text[-1] != "།" or diff_text[-1] != "༌":
            syls = get_syls(sr_diff_text)
            first_syl = syls[0]
            reformated_diff_text = f"[{diff_text}{first_syl},{right_diff_text}{first_syl}]"
            diffs[diff_walker+2][1] = "".join(syls[1:])
    return reformated_diff_text, diffs

def process_diff_text(chunk):
    reformated_diff = ""
    src_diff = re.search("\[(.+?),", chunk).group(1)
    trg_diff = re.search(",(.+?)\]", chunk).group(1)
    try:
        non_note_part = re.search("(.+)\[", chunk).group(1)
    except:
        non_note_part = ""
    if not non_note_part or non_note_part[-1] == "་" or non_note_part[-1] == "།" or non_note_part[-1] == " ":
        return chunk
    else:
        syls = get_syls(non_note_part)
        last_syl = syls[-1]
        reformated_diff = "".join(syls[:-1]) + f"[{last_syl}{src_diff},{last_syl}{trg_diff}]"
    return reformated_diff



def reformat_diff_text_from_left(text_with_diffs):
    text_with_diffs = re.sub("(\[.+?,.+?\])", "\g<1>\n", text_with_diffs)
    chunks = text_with_diffs.splitlines()
    reformated_diff_text = ""
    for chunk in chunks:
        if "]" in chunk:
            reformated_diff_text += process_diff_text(chunk)
        else:
            reformated_diff_text += chunk
    return reformated_diff_text

def reformat_continues_diff(text_with_diffs):
    reformated_text_with_diffs = text_with_diffs
    reformated_text_with_diffs = re.sub("\[([^\[|\]]+?),([^\]]+?)\]\[([^\[|\]]+?),([^\]]+?)\]", "[\g<1>\g<3>,\g<2>\g<4>]", reformated_text_with_diffs)
    return reformated_text_with_diffs

def rm_punct_note_text(oe_with_diffs):
    diffs = re.findall("\[.+?,.+?\]", oe_with_diffs)
    for diff in diffs:
        src_txt = re.search("\[(.+),", diff).group(1)
        trg_txt = re.search(",(.+)\]", diff).group(1)
        norm_src_txt = src_txt.replace(" ", "")
        norm_trg_txt = trg_txt.replace(" ", "")
        if norm_src_txt == norm_trg_txt:
            oe_with_diffs = oe_with_diffs.replace(diff, src_txt)
    return oe_with_diffs

def parse_diffs(diffs):
    oe_with_diffs = ""
    diffs = list(diffs)
    diff_list = []
    for diff in diffs:
        diff_list.append(list(diff))

    # left_diff = diffs[0]
    for diff_walker, (diff_type, diff_text) in enumerate(diff_list, 0):
        try:
            right_diff_type, right_diff_text = diff_list[diff_walker+1]
        except:
            right_diff_type, right_diff_text = [0, ""]
        if diff_type == 0:
            oe_with_diffs += diff_text
        elif diff_type == -1:
            if right_diff_type == 1 and "༑" not in right_diff_text:
                try:
                    second_right_diff = diff_list[diff_walker+2]
                except:
                    second_right_diff = [0, ""]
                reformated_diff_text, diff_list = reformat_diff_text_from_right(diff_text, right_diff_text, second_right_diff, diff_list, diff_walker)
                oe_with_diffs += reformated_diff_text
            else:
                oe_with_diffs += diff_text
    oe_with_diffs = reformat_diff_text_from_left(oe_with_diffs)
    oe_with_diffs = reformat_continues_diff(oe_with_diffs)
    oe_with_diffs = rm_punct_note_text(oe_with_diffs)
    return oe_with_diffs

def transfer_line_break(open_edition, oe_with_diffs):
    oe_with_diffs = oe_with_diffs.replace("\n" ,"")
    patterns = [['linebreak', "(\n)"]]
    oe_with_diffs = transfer(open_edition, patterns, oe_with_diffs)
    # oe_with_diffs = re.sub("(\[.+)\n([^\]]+\]?)", "\g<1>\g<2>\n", oe_with_diffs)
    return oe_with_diffs


def get_annotated_diffs(open_edition, diplomatic_edition):
    oe_with_diffs = ""
    normalised_oe = normalise_text(open_edition)
    normalised_de = normalise_text(diplomatic_edition)
    diffs = get_diffs(normalised_oe, normalised_de)
    dmp = dmp_module.diff_match_patch()
    diffs = list(diffs)
    dmp.diff_cleanupSemantic(diffs)
    oe_with_diffs = parse_diffs(diffs)
    oe_with_diffs = transfer_line_break(open_edition, oe_with_diffs)
    return oe_with_diffs


if __name__ == "__main__":
    open_edition = Path('./editions/OE.txt').read_text(encoding='utf-8')
    diplomatic_edition = Path('./editions/E4.txt').read_text(encoding='utf-8')
    open_edition_with_diffs = get_annotated_diffs(open_edition, diplomatic_edition)
    Path('./test.txt').write_text(open_edition_with_diffs, encoding='utf-8')
    
    # r = requests.post(url='https://openpecha.bdrc.io/api/v1/diff/', json={"textA": "༅། །བྱང་ཆུབ་སེམས་དཔའི", "textB": "༄། །བྱང་ཆུབ་སེམས་དཔའི་"})
    # diffs = r.json()
    # print(diffs)