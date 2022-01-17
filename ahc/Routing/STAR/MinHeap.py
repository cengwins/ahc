from heapq import heapify, heappush, heappop
from typing import Dict


class MinHeapNode:
    def __init__(self, key: int, data: Dict):
        self.key = key
        self.data = data

    def __eq__(self, o: object) -> bool:
        return self.key == o.key

    def __ne__(self, o: object) -> bool:
        return not self.key == o.key

    def __le__(self, other):
        return self == other or self < other

    def __lt__(self, other):
        return self.data['d'] < other.data['d']

    def __ge__(self, other):
        return self == other or self > other

    def __gt__(self, other):
        return self.data['d'] > other.data['d']

    def __str__(self):
        return f"#{self.key} / {self.data}"

    def __repr__(self):
        return f"#{self.key} / {self.data}"


class MinHeap:
    def __init__(self):
        self.heap = []
        heapify(self.heap)

    def insert(self, node):
        if node not in self.heap:
            heappush(self.heap, node)

    def print(self):
        print("The heap elements: ")

        for idx, i in enumerate(self.heap):
            print(f"{idx} => {i}")

    def extract_min(self) -> MinHeapNode:
        return heappop(self.heap)

    def is_empty(self) -> bool:
        return len(self.heap) == 0
