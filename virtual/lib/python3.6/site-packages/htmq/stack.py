
class Stack:

        def __init__(self):
                self.clear()


        def push(self, item):
                self._stack.append(item)


        def pop(self):
                item = self._stack[-1]
                del self._stack[-1]
                return item


        def clear(self):
                self._stack = []
