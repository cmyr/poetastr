# coding: utf-8
from __future__ import print_function
from __future__ import unicode_literals

import time
import json
import poetryutils2 as poetry
import os
import gzip

SAVE_DIR = os.path.expanduser('~/Documents/generated_poems')


def save_poem(poem):
    filename = "%s_%d" % (poem.poem_type,  time.time())
    filename = next_numbered_file(SAVE_DIR, filename, 'json.gz')
    write_json_to_gzip(filename, poem.to_dict())


def next_numbered_file(dir_path, basename, extension='txt.gz'):
    number_extension = 0
    while True:
        next_num = "%d" % number_extension if number_extension else ""
        nextname = os.path.join(dir_path, "%s%s.%s" %
                                (basename, next_num, extension))
        if not os.path.exists(nextname):
            return nextname
        number_extension += 1


def write_json_to_gzip(outfile, pyobj):
    with gzip.open(outfile, 'wb') as writefile:
        writefile.write(json.dumps(pyobj))


def tests():
    lines = [poetry.sorting.NormalizedLine(l, 'info') for l in
             ['line one', 'line two', 'line three']]
    poem = poetry.sorting.Poem('test-poem', lines)
    save_poem(poem)
    # this 'test' involves manually checking to see that the file was saved. :*


def main():
    pass


if __name__ == "__main__":
    tests()
    main()
