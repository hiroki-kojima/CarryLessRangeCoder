Python implementation of carry-less range coder
===================================================

Both static and dynamic encoding can be used.

Install
-------

.. code-block:: bash

   $ pip install CarryLessRangeCoder

Examples
--------

.. code-block:: python

    from collections import Counter
    import carryless_rangecoder as rc
    from io import BytesIO

    data = list(map(ord, 'qawsedrftgyhujikolp;'))
    count = [1] * 256
    for i, c in Counter(data).items():
        count[i] += c
    count_cum = [0] * 256
    for i in range(1, 256):
        count_cum[i] = count[i] + count_cum[i - 1]

    out = BytesIO()
    # Encode
    with rc.Encoder(out) as enc:  # or enc.finish()
        for index in data:
            enc.encode(count, count_cum, index)
    # Decode
    decoded = []
    with rc.Decode(out) as dec:  # or dec.start()
        for _ in range(len(data)):
            decoded.append(dec.decode(count, count_cum))

    assert decoded == data
