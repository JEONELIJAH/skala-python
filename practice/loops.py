for i, val in enumerate(["A", "B", "C"]):
    print(i, val)


for i in range(5):
    if i == 3:
        break
    print(i)
else:
    print("정상 종료")


fruits = ["apple", "banana", "cherry"]

for fruit in fruits:
    print(fruit)

for i in range(1, 10, 2):
    print(i)

total = 0

for i in range(1, 6):
    total += i

print("합: ", total)

for index, fruit in enumerate(fruits): # enumerate()는 인덱스와 값을 동시에 가져올 수 있다.
    print(index, fruit)

squares = [x*x for x in range(10) if x % 2 == 0] # 컴프리헨션
print(squares)

def fib(n):
    a, b = 0, 1
    for _ in range(n):
        yield a
        yield b
        a, b = b, a + b
result = list(fib(10))
print("yield 반환값 모음:", result)

upper_fruits = [fruit.upper() for fruit in fruits]
print(upper_fruits)

pairs = [(x, y) for x in range(1, 3) for y in range(3, 5)]
print(pairs)

squares = {}
for i in range(1, 6):
    squares[i] = i ** 2
print(squares)

squares = {i: i ** 2 for i in range(1, 6)}
print(squares)

fruit_prices = {"apple": 1000, "banana": 500, "cherry":2000}
discount_prices = {fruit: price * 0.9 for fruit, price in
fruit_prices.items()}
print(discount_prices)

keys = ["name", "age", "city"]
values = ["Alice", 25, "Seoul"]
person = {k: v for k, v in zip(keys, values)}
print(person)

numbers = [1, 2, 2, 3, 3, 4, 5]
unique_squares = {num ** 2 for num in numbers}
print(unique_squares)