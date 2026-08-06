import ast, dis

tree = ast.parse('x = a + b')
print(ast.dump(tree, indent=2))

def add(x, y): return x + y
dis.dis(add)