#!/usr/bin/python
import clang.cindex as c
from clang.cindex import CursorKind
import sys

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def within_file(strnm):
    def children_in_file(node):
        return (c for c in node.get_children() if str(c.location.file) == strnm)
    
    return children_in_file

def make_qualified_name(classCursor):
    names = [classCursor.spelling]
    c = classCursor
    while c.lexical_parent:
        c = c.lexical_parent
        names.append(c.spelling)
        
    names.reverse()
    return "::".join(names[1:])
    
def print_node(node):
    text = node.spelling or node.displayname
    kind = str(node.kind)
    print '{} {} {}'.format(kind, text, str(node.location.line))
    
def find_first(node, predicate, children_fun):
    assert(node)
    if predicate(node):
        return node
    else:
        for ch in children_fun(node):
            x = find_first(ch, predicate, children_fun)
            if x:
                return x
        return None


def find_all(node, predicate, children_fun):
    assert(node)
    ans = []
    if predicate(node):
        ans.append(node)
    
    for ch in children_fun(node):
        ans += find_all(ch, predicate, children_fun)
        
    return ans

def analyze_file(filename):
    tu = get_tu(filename)
    chfun = within_file(filename)
    coocs = get_all_cooc(tu.cursor, chfun)
    return coocs

def get_tu(filename):
    index = c.Index.create()
    tu = index.parse(filename, ['-x', 'c++', '-std=c++11'])
    return tu

classKinds = [CursorKind.CLASS_DECL, CursorKind.STRUCT_DECL]

def get_all_cooc(tu, children_fun):
    classes = find_all(tu, 
             lambda n : n.kind in classKinds,
             children_fun)
    
    return [(make_qualified_name(c), get_coocurrences(c, children_fun)) for c in classes]

def get_coocurrences(classnode, children_fun):
    
    # helps avoid correlating members and members of nested classes.
    def exclude_subclass(node):
        return [c for c in children_fun(node) if c.kind not in classKinds] 
    
    methods = find_all(classnode, 
                       lambda n: n.kind == CursorKind.CXX_METHOD, 
                       exclude_subclass)
    
    functions = find_all()
    
    fields = find_all(classnode, 
                      lambda f: f.kind == CursorKind.FIELD_DECL,
                      exclude_subclass)
    
    method_to_member = {}
    member_to_method = {}
    
    for m in methods:
        (m, mems) = get_member_tally(m, children_fun, fields)
        method_to_member[m] = mems
        for field in mems:
            if member_to_method.has_key(field):
                member_to_method[field].add(m)
            else:
                member_to_method[field] = set([m])
                
    cooc = {}
    for (v1,ms) in member_to_method.items():
        for m in ms:
            for v2 in method_to_member[m]:
                if not cooc.has_key((v1,v2)):
                    cooc[(v1,v2)] = 1
                else:
                    cooc[(v1,v2)] += 1
    
    return cooc

def significant_cooc(cooc, min, thresh):
    probs = {}
    for ((k1,k2), v) in cooc.items():
        if cooc[(k1,k1)] < min:
                continue
        else:
            pk2givenk1 = v/float(cooc[(k1,k1)])
        
            if  pk2givenk1 > thresh:
                probs[(k1,k2)] = pk2givenk1
    
    return probs


def pad_rows(rows):
    strlen = lambda elt:  len(str(elt))
    row_lengths = map(lambda row : map(strlen, row), rows)
    max_row = reduce(lambda r1,r2: [max(i,j) for i,j in zip(r1,r2)], row_lengths)
    pad_row = lambda row : [ ' '*(i -len(str(j))) + str(j) for (i,j) in zip(max_row, row) ]
    padded = map(pad_row, rows)
    return padded

def display_matrix_table(m):
    pairs = m.keys()
    
    left = set([l for (l,_) in pairs])
    counts = [(m[(v,v)],v) for v in left]
    ordered = [ vname for (_,vname) in  sorted(counts, reverse=True)]
    
    right = set([r for (_,r) in pairs])
    assert(left == right)
    
    rows = []
    rows.append([' '] + list(ordered))

    for r in ordered:
        total = m[(r,r)]
        acc = [r]
        for l in ordered:
            assert(m.get((l,r), 0) == m.get((r,l),0))

            lr = m.get((l,r), 0)
            if lr == 0:
                acc.append(" ")
            else:
                acc.append("%d/%d" % (lr, total))
            
        rows.append(acc)

    padded = pad_rows(rows)

    for r in padded:
        print r

def get_member_tally(method, children_fun, fields):
    vars = find_all(method, lambda n: n.kind == CursorKind.MEMBER_REF_EXPR, children_fun)
    field_names = map(lambda n: n.spelling, fields)
    names = map(lambda x : x.spelling, vars)
    names = filter(lambda n : n in field_names, names)
    return (method.spelling, set(names))
    
# #clang.cindex.Config.set_library_file('/usr/local/lib/libclang.so')
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: %s [header file name]" % sys.argv[0])
        sys.exit()
 
    cs = analyze_file(sys.argv[1])
    for (cl, m) in cs:
        print cl
        display_matrix_table(m)