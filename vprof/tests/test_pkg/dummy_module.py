def dummy_fib(n):
    a, b = 0, 1
    for _ in range(n):
        yield a
        a, b = b, a + b

list(dummy_fib(15))
