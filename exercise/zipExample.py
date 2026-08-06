names = ["Alice", "Bob", "Charlie"]
ages = [25, 30, 35]
zipped = zip(names, ages)
print(list(zipped))

for name, age in zip(names, ages):
    print(f"{name}의 나이는 {age}살입니다.")

keys = ["name", "age", "city"]
values = ["Alice", 25, "Seoul"]
person = dict(zip(keys, values))
print(person)

pairs = [("Alice", 25), ("Bob", 30), ("Charlie", 35)]
names, ages = zip(*pairs) # 언패킹
print(names) # ('Alice', 'Bob', 'Charlie')
print(ages)

students = ["Alice", "Bob", "Charlie"]
scores = [90, 80, 95]
sorted_students = [name for name, _ in sorted(zip(scores, students), reverse=True)]
print(sorted_students)

a = [1, 2, 3]
b = ["one", "two"]
print(list(zip(a, b))) # [(1, 'one'), (2, 'two')]

from itertools import zip_longest
print(list(zip_longest(a, b, fillvalue="없음")))

columns = ["이름", "나이", "도시"]
rows = [
    ["Alice", 25],
    ["Bob", 30, "Seoul"],
    ["Charlie"] 
]

formatted_rows = [list(zip_longest(columns, row, fillvalue="정보 없음")) for row in rows]
print(formatted_rows)
for row in formatted_rows:
    print(dict(row))