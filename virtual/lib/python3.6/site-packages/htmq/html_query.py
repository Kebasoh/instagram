from copy import copy
from functools import partialmethod

from .html_parser import HtmlParser
from .stack import Stack


def dbg(): import pdb; pdb.set_trace()


class Range:

        def __init__(self):
                self._indices = set()
                self._multi_result = True


        def first(self, n=1):
                self._multi_result = n > 1 or len(self._indices) > 0
                for i in range(0, n):
                        self._indices.add(i)


        def last(self, n=1):
                self._multi_result = n > 1 or len(self._indices) > 0
                for i in range(n, 0, -1):
                        self._indices.add(-i)


        def nth(self, n):
                self._multi_result = len(self._indices) > 0
                self._indices.add(n)


        def apply(self, list_in):
                if len(self._indices) == 0:
                        return copy(list_in)


                list_len = len(list_in)
                self.convert_neg_indices(list_len)

                list_out = []
                for i in sorted(self._indices):
                        if i < list_len:
                                list_out.append(list_in[i])

                return list_out


        def convert_neg_indices(self, list_len):
                rem = []
                for i in range(0, len(self._indices)):
                        if i < 0:
                                self.indices.add(list_len + i)
                                rem.append(i)
                for r in rem:
                        self._indices.remove(r)


        def is_single_result(self):
                return not self._multi_result

        
        def set_single_result(self, value):
                self._multi_result = not value

        
        single_result = property(is_single_result, set_single_result)


class Attr:
        text = lambda e : e.text
        attr = lambda a : lambda e : e.attrib.get(a, None)

        def __init__(self):
                self._attrs = []


        def add(self, a):
                self._attrs.append(a)


        def get(self, e):
                res = ()
                for a in self._attrs:
                        val = a(e)
                        val = val.strip() if val is not None else None
                        res += (val,)

                return res

class HtmlQuery:

        def __init__(self, html):
                self._html = html
                self._parser = None
                self._etree = None

                self._stack = Stack()

                self.clear()

        def clear(self):
                self._path = '.'
                self._exc_cls = None
                self._exc_ret = None
                self._range = Range()
                self._result = None
                self._attr = []
                self._skip = []
                self._attr = Attr()

                self._stack.clear()


        def all(self):
                self._path += '/'
                return self


        def div(self, cls=None, id=None):
                self._path += '/div'
                self._path += "[@class='%s']"%cls if cls is not None else ''
                self._path += "[@id='%s']"%id if id is not None else ''

                return self

        def tag(self, name, cls=None, id=None):
                self._path += '/' + name
                self._path += "[@class='%s']"%cls if cls is not None else ''
                self._path += "[@id='%s']"%id if id is not None else ''

                return self

        def span(self, cls=None, id=None):
                self._path += '/span'
                self._path += "[@class='%s']"%cls if cls is not None else ''
                self._path += "[@id='%s']"%id if id is not None else ''

                return self

        def body(self):
                pass


        def a(self, cls=None, id=None):
                self._path += '/a'
                self._path += "[@class='%s']"%cls if cls is not None else ''
                self._path += "[@id='%s']"%id if id is not None else ''

                return self


        def on_exc(self, ret=None, exc_cls=None):
                self._exc_cls = exc_cls
                self._exc_ret = ret
                return self


        def first(self, n=1):
                self._range.first(n=n)
                return self


        def last(self, n=1):
                self._range.last(n=n)
                return self


        def one(self):
                self._range.nth(0)
                return self


        def title(self):
                self._path = ".//title"
                self._range.single_result = True
                return self


        def parse(self):
                pass


        def skip(self, tag):
                self._skip.append(tag)
                return self


        def evaluate(self):
                parser = HtmlParser(skip_tags=self._skip)
                parser.feed(self._html)
                self._etree = parser.etree

                elements = self._etree.findall(self._path)
                self.filter(elements)


        def filter(self, elements):
                r_elements = None
                if elements is not None and len(elements) > 0:
                        r_elements = self._range.apply(elements)
                else:
                        return None

                self._result = []
                for e in r_elements:
                        r = self._attr.get(e)
                        if len(r) > 0:
                                self._result.append(r if len(r) > 1 else r[0])       
                        else:
                                self._result.append(e)


        def text(self):
                self._attr.add(Attr.text)
                return self


        def attr(self, name):
                self._attr.add(Attr.attr(name))
                return self


        def attrs(self, names):
                for n in names.split(','):
                        self._attr.add(Attr.attr(n.strip()))
                return self


        def done(self):
                self.evaluate()
                res = self._result

                if res is None:
                        if self._exc_cls is not None:
                                raise self._exc_cls()
                        elif self._exc_ret is not None:
                                res = self._exc_ret
                        else:
                                pass
                else:
                        if self._range.single_result:
                                res = self._result[0]
                        else:
                                res = self._result

                self.clear()
                return res


        def q(self):
                return self.done()


        def nth(self, n=1):
                self._range.nth(n)
                return self


        second = partialmethod(nth,1)
        third = partialmethod(nth, n=2)
        fourth = partialmethod(nth, n=3)

        #img =
        #span =
        #etc.

        input = partialmethod(tag, 'input')

        #def regex()

        #def start()
        #def end()

        #def n()

        #element query

        #if text eq., then query further

def htmq(html):
        hq = HtmlQuery(html)
        return hq
