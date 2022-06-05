#!/opt/homebrew/bin/python3

import sys
import collections
import CppHeaderParser
import clang.cindex
from fuzzywuzzy import fuzz
import re

Ref = collections.namedtuple("Ref", ["line", "col", "value"])

def find_typerefs(tu, patterns):
    """ Find all references to the type named 'typename'
    """
    result = {}
    for t in tu.get_tokens(extent=tu.cursor.extent):
        if (t.kind == clang.cindex.TokenKind.IDENTIFIER):
            if t.spelling in patterns:
                if t.spelling in result.keys():
                    result[t.spelling].append(Ref(t.location.line, t.location.column, t.spelling))
                else:
                    result[t.spelling] = [Ref(t.location.line, t.location.column, t.spelling)]
    return result


def find_all_definations(path):
    result = set()
    try:
        cppHeader = CppHeaderParser.CppHeader(path)
        result.update(set(cppHeader.classes.keys()))
        result.update(set([re.split(' |\(|\)', item)[0] for item in cppHeader.defines]))
        result.update(set([item["name"] for item in cppHeader.enums]))
        result.update(set(cppHeader.structs.keys()))
        result.update(set(cppHeader.typedefs.keys()))
        result.update(set([item["name"] for item in cppHeader.variables]))
        result.update(set([item["name"] for item in cppHeader.functions]))
        return result
    except CppHeaderParser.CppParseError as e:
        print("cpp header %s parse error: %s" % (path, str(e)))
        return result


if __name__ == '__main__':
    src_file = sys.argv[1]
    compared_header = sys.argv[2]
    print('Searching dependencies for %s in %s' % (src_file, compared_header))
    search_keywords = find_all_definations(compared_header)

    print(search_keywords)
    
    idx = clang.cindex.Index.create()
    tu = idx.parse(src_file)
    result = find_typerefs(tu, search_keywords)

    for key in result.keys():
        if result[key] and len(result[key]) != 0:
            print("%s: "%(key))
            print("[")
            for v in result[key]:
                print("    "+ str(v))
            print("]")
