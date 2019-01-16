# encoding: utf-8
# output函数
def output(string):
    print(string)

# add函数
def add(x, y):
    z = x + y
    output(str(z)) # 调用output函数
    return z

a = 2
b = 3

# 调用add函数
sum = add(a, b)

# if分支
if sum < 10 or sum>100:
    print("if true")
else:
    print("if false")

# 循环
for i in range(5):
    print(i)

