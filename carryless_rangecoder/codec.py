"""Python implementation of carry-less range coder.

Examples
--------
>>> from collections import Counter
>>> from io import BytesIO
>>> data = list(map(ord, 'qawsedrftgyhujikolp;'))
>>> count = [1] * 256
>>> for i, c in Counter(data).items():
...     count[i] += c
...
>>> count_cum = [0] * 256
>>> count_cum[0] = count[0]
>>> for i in range(1, 256):
...     count_cum[i] =  count[i] + count_cum[i - 1]
...
>>>

with context manager.

>>> out = BytesIO()
>>> with Encoder(out) as enc:
...     for index in data:
...         enc.encode(count, count_cum, index)
...
>>> decoded = []
>>> with Decoder(out) as dec:
...     for _ in range(len(data)):
...         decoded.append(dec.decode(count, count_cum))
...
>>> assert decoded == data

without context manager.

>>> out = BytesIO()
>>> enc = Encoder(out)
>>> for index in data:
...     enc.encode(count, count_cum, index)
>>> enc.finish()
>>> decoded = []
>>> dec = Decoder(out)
>>> dec.start()
>>> for _ in range(len(data)):
...     decoded.append(dec.decode(count, count_cum))
>>> assert decoded == data

"""
from typing import BinaryIO
from typing import Iterable


class _Base(object):
    def __init__(self, stream: BinaryIO, range_size: int = 64,
                 precision: int = 8, endian: str = 'big'):
        self.stream = stream
        self._range_size = range_size
        self._precision = precision
        self._endian = endian

        self._top = 1 << range_size - precision
        self._bot = 1 << range_size - precision * 2

        self._low = 0
        self._range = (1 << range_size) - 1

    def _update_range(self, get_or_put):
        while self._low ^ (self._low + self._range) < self._top:
            get_or_put()
            self._range <<= self._precision
            self._low <<= self._precision

        while self._range < self._bot:
            get_or_put()
            self._range = (-self._low & (self._bot - 1)) << self._precision
            self._low <<= self._precision


class Encoder(_Base):
    def __init__(self, *args, **kwargs):
        """The encoder of carry-less rangecoder.

        Parameters
        ----------
        stream: BinaryIO
            Output stream.
        range_size: int, optional
            Range size [bits] (default is 64).
        precision: int, optional
            Must be multiple of 8 [bits] (default is 8).
        endian: str, {'big', 'little'}
            Default is 'big'.

        """
        super(Encoder, self).__init__(*args, **kwargs)
        self._mask = (1 << self._precision) - 1

    def _to_bytes(self, i):
        return i.to_bytes(self._precision // 8, self._endian)

    def _put(self):
        i = (self._low >> (self._range_size - self._precision))
        self.stream.write(self._to_bytes(i & self._mask))

    def encode(self, count: Iterable[int], count_cum: Iterable[int], index: int
               ) -> None:
        """Encode a symbol.

        Parameters
        ----------
        count: array_like of int
        count_cum: array_like of int
        index: int

        """
        self._range //= count_cum[-1]
        self._low += (count_cum[index - 1] if index else 0) * self._range
        self._range *= count[index]

        self._update_range(self._put)

    def finish(self):
        self.__exit__()

    def __enter__(self):
        return self

    def __exit__(self, *_, **__):
        for _ in range(0, self._range_size, self._precision):
            self._put()
            self._low <<= self._precision

        return False


class Decoder(_Base):
    def __init__(self, *args, **kwargs):
        """The decoder of carry-less range coder.

        Parameters
        ----------
        stream: BinaryIO
            Input stream.
        range_size: int, optional
            Range size [bits] (default is 64).
        precision: int, optional
            Must be multiple of 8 [bits] (default is 8).
        endian: str, {'big', 'little'}
            Default is 'big'.

        """
        super(Decoder, self).__init__(*args, **kwargs)
        self.stream.seek(0)
        self._code = 0

    def _from_bytes(self, b):
        return int.from_bytes(b, self._endian)

    def _get(self):
        b = self.stream.read(self._precision // 8)
        self._code = (self._code << self._precision) + self._from_bytes(b)

    def decode(self, count: Iterable[int], count_cum: Iterable[int]) -> int:
        """Decode a symbol.

        Parameters
        ----------
        count: array_like of int
        count_cum: array_like of int

        Returns
        -------
        index: int

        """
        self._range //= count_cum[-1]

        target = (self._code - self._low) // self._range
        left, right = 0, (1 << self._precision) - 1
        while left < right:
            middle = (left + right) // 2
            if count_cum[middle] <= target:
                left = middle + 1
            else:
                right = middle

        self._low += (count_cum[left - 1] if left else 0) * self._range
        self._range *= count[left]

        self._update_range(self._get)

        return left

    def start(self):
        self.__enter__()

    def __enter__(self):
        for _ in range(0, self._range_size, self._precision):
            self._get()

        return self

    def __exit__(self, *_, **__):
        return False
