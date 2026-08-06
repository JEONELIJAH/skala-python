from collections import deque

queue = deque([1, 2, 3])
queue.append(4)
queue.appendleft(0)
print(deque)

queue.pop()
queue.popleft()
print(queue)