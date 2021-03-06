import string
import json
from pprint import pprint
import os.path

class ParseException(Exception):
    pass

def extract_token(s):
    pos = 0
    quoted_string = False
    # find end of whitespace
    while pos < len(s) and s[pos] in string.whitespace:
        pos += 1
    if pos >= len(s) - 1:
        return None, ""

    # is this a "?
    if s[pos] == '"':
        quoted_string = True

    end_pos = pos + 1
    # find end of text
    while end_pos < len(s) and ((not quoted_string and s[end_pos] not in string.whitespace) or \
          (quoted_string and s[end_pos] != '"')):
        end_pos += 1
    if end_pos >= len(s):
        raise ParseException("Trailing garbage found: %s" % (s, ))

    token = s[pos:end_pos]
    rest = s[end_pos:]
    if quoted_string:
        token = s[pos + 1:end_pos].decode("string_escape")
        rest = s[end_pos + 1:]

    
    return token, rest

S_WAITING_KEY = 0
S_WAITING_VALUE = 1
S_WAITING_DICT_NAME = 2

def new_ctx():
    return dict(current_key="", tree=dict())

def parse_tree(sq):
    # retain backwards compatibility if needed
    if type(sq) is str:
        sq = (sq,)

    tree_depth = 0
    state = S_WAITING_KEY
    ctx = [new_ctx()]
    cur_ctx = ctx[0]
    for s in sq:
        # s is a string containing data to parse
        while True:
            # find key: first non-whitespace char
            token_value, s = extract_token(s)
    
            # None is the "no more tokens" sentinel value
            if token_value is None:
                break
    
            if state is S_WAITING_KEY and token_value == "BEGIN":
                state = S_WAITING_DICT_NAME
            elif state is S_WAITING_KEY and token_value == "END":
                old_ctx = ctx.pop(0)
                cur_ctx = ctx[0]
                if cur_ctx["current_key"] in cur_ctx["tree"]:
                    if type(cur_ctx["tree"][cur_ctx["current_key"]]) is not list:
                        cur_ctx["tree"][cur_ctx["current_key"]] = [cur_ctx["tree"][cur_ctx["current_key"]], old_ctx["tree"]]
                    else:
                        cur_ctx["tree"][cur_ctx["current_key"]].append(old_ctx["tree"])
                else:
                    cur_ctx["tree"][cur_ctx["current_key"]] = old_ctx["tree"]
            elif state is S_WAITING_DICT_NAME:
                cur_ctx["current_key"] = token_value
                state = S_WAITING_KEY
                ctx.insert(0, new_ctx())
                cur_ctx = ctx[0]
            elif state is S_WAITING_KEY:
                cur_ctx["current_key"] = token_value
                state = S_WAITING_VALUE
            elif state is S_WAITING_VALUE:
                cur_ctx["tree"][cur_ctx["current_key"]] = token_value
                state = S_WAITING_KEY
                cur_ctx["current_key"] = None 
    if tree_depth != 0:
        raise ParseException("Tree not completely unwound")
    return cur_ctx["tree"]
        

def parse_save(f):
    # .prison files are key-value pairs
    prison = parse_tree(f)
    return prison

def parse_save_from_file(fn, cache=True):
    # .prison files may take substantial time to load
    cache_fn = os.path.join("prison_cache", os.path.abspath(fn).replace("/", "_")) # how do you get the path separator?...
    if cache and os.path.exists(cache_fn):
        with open(cache_fn, 'r') as cache_file:
            return json.load(cache_file)
    
    with open(fn, 'r') as prison_file:
        prison = parse_save(prison_file)

    if cache and os.path.exists("prison_cache"):
        if not os.path.exists("prison_cache"):
            os.makedirs(os.path.dirname(cache_fn))
        with open(cache_fn, 'w') as cache_file:
            json.dump(prison, cache_file)

    return prison

if __name__ == '__main__':
    pprint(parse_save(open("start01.prison", "r")))
