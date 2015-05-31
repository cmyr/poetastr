# coding: utf-8
from __future__ import print_function
from __future__ import unicode_literals

import random
from collections import deque

class IterCombiner(object):
    """
    takes a base iterator and allows other items to be mixed in 
    with its results. Mixin is random, with the ratio of other items
    determined by the `ratio` argument.
    """

    def __init__(self, base_iter, other_items=None, ratio=0.5):
        super(IterCombiner, self).__init__()
        self.base_iter = iter(base_iter)
        self._other_items = deque()
        self.use_other = False
        self.ratio = ratio
        if other_items:
            self.add_items(other_items)

    def __iter__(self):
        return self

    def next(self):
        if self.use_other and random.random() <= self.ratio:
            try:
                item = self._other_items.popleft()
                return item
            except IndexError as err:
                self.use_other = False
        return self.base_iter.next()

    def add_items(self, items):
        self._other_items.extend(items)
        self.use_other = True


def main():

    items = [i for i in range(30)]
    mixin = list('abcdefghijkl')

    combiner = IterCombiner(items)
    for i in combiner:
        print(i)
        if i == 10:
            combiner.add_items(mixin)



if __name__ == "__main__":
    main()