def dummy_fib(n):
    if n < 2:
        return n
    return dummy_fib(n - 1) + dummy_fib(n - 2)
