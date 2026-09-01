def countdown(n):
    while n > 0:
        yield n
        n -= 1

gen = countdown(3)

print(next(gen))  # Output: 3
print(next(gen))  # Output: 2
print(next(gen))  # Output: 3rd value (1)


# The next call raises StopIteration to signal completion