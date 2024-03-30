"""Priority queue."""
from typing import Any, Optional
from math import log


class PriorityQueue:
    """A priority queue implemented by binary min heap.
    """
    _heap: list[Any]
    _priority: dict[Any, int | float]
    _idx: dict[Any, int]

    def __init__(self, items: Optional[dict[Any, int | float]] = None) -> None:
        if items is not None:
            self._heap = list(items.keys())
            self._priority = items.copy()
            self._idx = {self._heap[i]: i for i in range(len(self._heap))}
            self._heapify()
        else:
            self._heap = []
            self._priority = {}
            self._idx = {}

    def __len__(self) -> int:
        return len(self._heap)

    def __contains__(self, item):
        return item in self._priority

    def __str__(self) -> str:
        res = ''
        n = len(self._heap)
        for i in range(n):
            res += str(self._heap[i]) + ' '
            m = log(i + 2, 2)
            if m == int(m):
                res += '\n'
        return res

    def is_empty(self) -> bool:
        """Whether the queue is empty.
        """
        return len(self._heap) == 0

    def get_priority(self, item: Any) -> int | float:
        """Get the priority of item. Raise ValueError if item is not in the queue.
        """
        if item not in self._priority:
            raise ValueError
        else:
            return self._priority[item]

    def enqueue(self, item: Any, priority: int | float) -> None:
        """Enqueue an item with the priority.
        Raise ValueError if the item is already in the priority queue.
        """
        if item in self._priority:
            raise ValueError("Item is already in the priority queue.")
        else:
            n = len(self._heap)
            self._heap.append(item)
            self._priority[item] = priority
            self._idx[item] = n
            i, j = n, self._shift_up(n)
            while j < i:
                i = j
                j = self._shift_up(j)

    def dequeue(self) -> Any:
        """Pop the item with MINIMUM priority.
        Raise ValueError if the queue is empty.
        """
        if self.is_empty():
            raise ValueError
        else:
            n = len(self._heap)
            self._heap[0], self._heap[n - 1] = self._heap[n - 1], self._heap[0]
            res = self._heap.pop()
            self._priority.pop(res)
            self._idx.pop(res)
            if len(self._heap) > 0:
                self._idx[self._heap[0]] = 0
                i, j = 0, self._shift_down(0)
                while j > i:
                    i = j
                    j = self._shift_down(j)
            return res

    def update_priority(self, elem: Any, new_priority: int | float) -> None:
        """Update the priority of elem.
        Raise ValueError if elem is not in the queue
        """
        if elem not in self._priority:
            raise ValueError
        else:
            prev_priority = self._priority[elem]
            self._priority[elem] = new_priority
            if new_priority < prev_priority:
                i = self._idx[elem]
                j = self._shift_up(i)
                while j < i:
                    i = j
                    j = self._shift_up(j)
            elif new_priority > prev_priority:
                i = self._idx[elem]
                j = self._shift_down(i)
                while j > i:
                    i = j
                    j = self._shift_down(j)

    def _heapify(self) -> None:
        """Bottom up heapify self.heap.

        Preconditions:
            - not self.is_empty()
        """
        n = len(self._heap)
        for i in range((n - 2) // 2, -1, -1):
            k, j = i, self._shift_down(i)
            while k < j:
                k = j
                j = self._shift_down(j)

    def _shift_down(self, idx: int) -> int:
        """Shift down self._heap[idx] and return the resultant index of
        the element that was originally self._heap[idx].

        Preconditions:
           - not self.is_empty()
           - 0 <= idx < len(self.heap)
        """
        n = len(self._heap)
        left = 2 * idx + 1
        right = 2 * idx + 2
        smallest_idx = idx
        if left < n and self._priority[self._heap[left]] < self._priority[self._heap[idx]]:
            smallest_idx = left
        if right < n and self._priority[self._heap[right]] < self._priority[self._heap[smallest_idx]]:
            smallest_idx = right
        if smallest_idx != idx:
            self._heap[idx], self._heap[smallest_idx] = self._heap[smallest_idx], self._heap[idx]
            self._idx[self._heap[idx]], self._idx[self._heap[smallest_idx]] = idx, smallest_idx
        return smallest_idx

    def _shift_up(self, idx: int) -> int:
        """Shift up self._heap[idx] and return the resultant index of the
        element that was originally self._heap[idx].

        Preconditions:
            - not self.is_empty()
            - 0 <= idx < len(self.heap)
        """
        parent_idx = (idx - 1) // 2
        if parent_idx >= 0 and self._priority[self._heap[idx]] < self._priority[self._heap[parent_idx]]:
            self._heap[idx], self._heap[parent_idx] = self._heap[parent_idx], self._heap[idx]
            self._idx[self._heap[idx]], self._idx[self._heap[parent_idx]] = idx, parent_idx
            return parent_idx
        else:
            return idx
