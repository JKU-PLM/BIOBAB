import collections
import heapq

# this is where we store our nodes during tree search
class Queue:
    def __init__(self, mode):
        if mode == 'best':
            self.queue = []
        else:
            self.queue = collections.deque()
        self.mode = mode

    def push(self, item):
        if self.mode == 'best':
            heapq.heappush(self.queue, (item.score, item) )
        else:
            self.queue.append(item)

    def pop(self):
        if self.mode == 'lifo':
            return self.queue.pop()
        elif self.mode == 'fifo':
            return self.queue.popleft()
        elif self.mode == 'best':
            return heapq.heappop(self.queue)[1]
        else:
            print('unknown processing mode:', self.mode)

    def __len__(self):
        return len(self.queue)

    def empty(self):
        return len(self.queue) == 0

