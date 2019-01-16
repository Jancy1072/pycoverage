# encoding: utf-8
import marshal, types, os, sys
import linecache
import re

# pyc文件的处理
class PycFile:
    # 读取pyc文件
    def read(self, f):
            f = open(f, "rb")
            self.magic = f.read(4) # 标识此pyc的版本信息
            self.modtime = f.read(4) # pyc产生的时间
            self.code = marshal.load(f) # 序列化了的PyCodeObject
            self.lines = 0 # 可执行的总行数
            self.lineno = [] # 可执行的行号

    # 统计可执行的总行数、可执行的行号
    def count_lines(self):
        self.lines, self.lineno = count_lines(self.code, self.lines, self.lineno)
        self.lines += 1
        # print(self.lineno)

# 统计可执行的总行数、可执行的行号
def count_lines(code, lines, lineno):
    lines += len(code.co_lnotab) / 2 # 利用行号表统计可执行的行数、行号
    firstno = code.co_firstlineno
    lb_ranges = [ord(code.co_lnotab[b * 2 + 1]) for b in range(len(code.co_lnotab) / 2)]
    lineno.append(firstno)
    for lb in lb_ranges:
        firstno += lb
        lineno.append(firstno)

    for const in code.co_consts:
        if type(const) == types.CodeType:
            lines, lineno = count_lines(const, lines, lineno) # 递归
    return lines, lineno

def analyse_file(file_name, pyc_file_name):
    result = "" # 存储所有要写入文件的字符串
    pyc = PycFile() # 实例化一个pyc对象
    pyc.read(pyc_file_name) # 读取pyc文件
    pyc.count_lines() # 调用函数，来统计可执行的总行数、可执行的行号
    executable_length = pyc.lines #可执行的总行数

    f = open("coverage.txt", "r") # 读取coverage.txt中的中间结果
    f.readline()

    # 函数覆盖率
    function_all = f.readline()[:-1] # 所有函数
    function_call_tuple = f.readline()[:-1] # 函数调用关系

    call_tree = {} # 函数调用树
    not_call = [] # 没有被调用的函数
    function_ratio = 0 # 初始化函数覆盖率
    function_call_set = []
    if len(function_all) and len(function_call_tuple):
        function_call = [] # 调用的函数
        new_function_call_tuple = []

        # 字符串处理以计数
        function_all = function_all.split(",")
        function_call_tuple = function_call_tuple.split(";")

        for i in function_call_tuple:
            tmp = re.sub(r'\(|\)|\s|\'', "", i)
            tmp = tuple(tmp.split(","))

            new_function_call_tuple.append(tmp)
            function_call.append(tmp[1])

        function_call_set = list(set(function_call))

        for i in function_all:
            if i not in function_call_set:
                not_call.append(i)

        for i in new_function_call_tuple:
            if i[0] in call_tree:
                pass
            else:
                call_tree[i[0]] = []
            call_tree[i[0]].append(i[1])

        function_ratio = float(len(function_call_set)) / len(function_all) * 100

    print("call: " + str(function_call_set))
    print("call tree: " + str(call_tree))
    print("not cal: " + str(not_call))
    print("function coverage: " + str(function_ratio) + "%")
    print("\n")

    result += "call: " + str(function_call_set) + "\n"
    result += "call tree: " + str(call_tree) + "\n"
    result += "not cal: " + str(not_call) + "\n"
    result += "call number: " + str(len(function_call_set)) + "\n"
    result += "not call number: " + str(len(not_call)) + "\n"
    result += "function coverage: " + str(function_ratio) + "%" + "\n"
    result += "\n\n"

    # 语句覆盖率
    lines_executed = f.readline()[:-1]
    statement_ratio = 0
    if len(lines_executed):
        lines_executed = lines_executed.split(",")
        executed_length = len(set(lines_executed))
        statement_ratio = float(executed_length) / executable_length * 100

    print("executable lines: " + str(executable_length))
    print("executed lines: " + str(executed_length))
    print("missing lines: " + str(executable_length - executed_length))
    print("statement coverage: " + str(statement_ratio) + "%")
    print("\n")

    result += "executable lines: " + str(executable_length) + "\n"
    result += "executed lines: " + str(executed_length) + "\n"
    result += "missing lines: " + str(executable_length - executed_length) + "\n"
    result += "statement coverage: " + str(statement_ratio) + "%" + "\n"
    result += "\n\n"

    # 分支覆盖率
    new_pairs_executed_tuple = []
    pairs_executed_tuple = f.readline()[:-1]
    f.close()
    missbranch = 0 # 没有执行的分支
    branch_count = 0 # 总的分支数
    branch_ratio = 0
    if len(pairs_executed_tuple):
        # 字符串处理以计数
        pairs_executed_tuple = pairs_executed_tuple.split(";")

        for i in pairs_executed_tuple:
            tmp = re.sub(r'\(|\)|\s|\'', "", i)
            tmp = tuple(int(j) for j in tmp.split(","))
            new_pairs_executed_tuple.append(tmp)

            pairs_executed_tuple_set = list(set(new_pairs_executed_tuple))

        for i in pairs_executed_tuple_set:
            target = i[0]
            target_count = 0
            for j in pairs_executed_tuple_set:
                if target == j[0]:
                    target_count += 1
            if target_count < 2: # 如果小于两个分支
                missbranch += 1

        # 统计总的分支数
        keyword_count = 0
        for i in pyc.lineno:
            prestatement = linecache.getline(file_name, i)
            prestatement_parts = re.split("\s|\(|\,|\)|\:", prestatement)
            for word in prestatement_parts:
                if "if" == word or "elif" == word or "for" == word or "while" == word:
                    keyword_count += 1
                    break

        branch_count = keyword_count * 2
        branch_ratio = float(branch_count - missbranch) / branch_count * 100

    print("branch: " + str(branch_count))
    print("missing branch: " + str(missbranch))
    print("branch coverage: " + str(branch_ratio) + "%")
    result += "branch: " + str(branch_count) + "\n"
    result += "missing branch: " + str(missbranch) + "\n"
    result += "branch coverage: " + str(branch_ratio) + "%" + "\n"
    result += "\n\n"

    # 将函数覆盖率、语句覆盖率、分支覆盖率写入文件
    f = open("analyse_result.txt", "w+")
    f.write(result)
    f.close()
    print("\nanalyse_result.txt is created to store analysis result.")


try:
    f = open("coverage.txt", "r")
except IOError:
    print("coverage.txt is not found.")
else:
    file_name = f.readline()[:-1]
    f.close()

    if os.path.exists(file_name):
        pass
    else:
        print(file_name + " is not found.")
        sys.exit(1)

    pyc_file_name = file_name + "c"
    if os.path.exists(pyc_file_name):
        pass
    else:
        print(pyc_file_name + " is not found.")
        sys.exit(1)

    analyse_file(file_name, pyc_file_name)




