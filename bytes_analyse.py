# encoding: utf-8
import marshal, types, new, sys, os
from opcode import *

# pyc文件的处理
class PycFile:
    def read(self, f):
        f = open(f, "rb")

        self.magic = f.read(4) # 标识此pyc的版本信息
        self.modtime = f.read(4) # pyc产生的时间
        self.code = marshal.load(f) # 序列化了的PyCodeObject
        self.byte_all = [] # 所有字节码的所有信息

    # 统计字节码，并修改pyc文件内容
    def change_line_numbers(self):
        self.code, self.byte_all = change_line_numbers(self.code, self.byte_all)

    # 写入pyc文件
    def write(self, f):
        if isinstance(f, basestring):
            f = open(f, "wb+")
        f.write(self.magic)
        f.write(self.modtime)
        marshal.dump(self.code, f)

# 统计字节码，并修改pyc文件内容
def change_line_numbers(code, byte_all):
    n_bytes = len(code.co_code) # 字节码

    codelist = [ord(i) for i in list(code.co_code)] # 将字节码转为十进制
    index = 0
    extended_arg = 0
    free = None
    while index < n_bytes: # 遍历字节码
        value = codelist[index]
        byte_all.append([(code.co_name, index), opname[value]]) # 获取字节码所在函数名、索引、指令名
        op = codelist[index]
        print code.co_name, index,
        print opname[value].rjust(5),
        index += 1 # 字节码大于等于90，则有参数，占3个字节；小于90，不含参数，占1个字节
        if value >= HAVE_ARGUMENT: # HAVE_ARGUMENT = 90
            # 处理参数信息
            oparg = codelist[index] + codelist[index + 1] * 256 + extended_arg
            extended_arg = 0
            index += 2
            if op == EXTENDED_ARG:
                extended_arg = oparg * 65536L

            # print repr(oparg).rjust(5),
            # byte_all[-1].append(oparg)
            if op in hasconst:
                print('(' + repr(code.co_consts[oparg]) + ')')
                byte_all[-1].append(repr(code.co_consts[oparg]))
            elif op in hasname:
                print('(' + code.co_names[oparg] + ')')
                byte_all[-1].append(code.co_names[oparg])
            elif op in hasjrel:
                print('(to ' + repr(index + oparg) + ')')
                byte_all[-1].append(repr(index + oparg))
            elif op in haslocal:
                print('(' + code.co_varnames[oparg] + ')')
                byte_all[-1].append(code.co_varnames[oparg])
            elif op in hascompare:
                print('(' + cmp_op[oparg] + ')')
                byte_all[-1].append(cmp_op[oparg])
            elif op in hasfree:
                print('(' + free[oparg] + ')')
                byte_all[-1].append(free[oparg])
            else:
                print("")
        else:
            print("")

    # 修改行号表，使得能够每个字节码触发一次追踪行数
    new_lnotab = "\x01\x01" * (n_bytes - 1)

    new_consts = []
    for const in code.co_consts:
        if type(const) == types.CodeType:
            const, byte_all = change_line_numbers(const, byte_all)
            new_consts.append(const)
        else:
            new_consts.append(const)
    # 构造新的字节码
    new_code = new.code(
        code.co_argcount, code.co_nlocals, code.co_stacksize, code.co_flags,
        code.co_code, tuple(new_consts), code.co_names, code.co_varnames,
        code.co_filename, code.co_name, 0, new_lnotab
    )
    return new_code, byte_all

# 自定义追踪函数
def trace(frame, event, arg):
    global file_name
    global byteno
    global byte_all_content
    if event == 'line':
        code = frame.f_code

        file_name = code.co_filename

        if file_name == file_name:
            function_name = code.co_name # 所在函数名
            line_no = frame.f_lineno # 行号（字节码索引）
            # print(function_name, line_no)
            byteno.append((function_name, line_no))

    return trace

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

    pyc = PycFile()
    pyc.read(pyc_file_name)

    # byte coverage

    print("***************All bytes***************")
    pyc.change_line_numbers()
    print("***************************************\n")

    pyc.write(pyc_file_name)
    byte_all = len((pyc.byte_all)) # 字节码总数
    byte_all_content = pyc.byte_all # 字节码所有信息
    byteno = [] # 执行的字节码信息
    file_name = file_name.split("/")[-1]
    file_name = file_name.replace(".py", "")
    sys.settrace(trace)

    __import__(file_name)
    executed_set = list(set((byteno)))
    executed_count = len(executed_set) # 执行的字节码数量

    print("***************Missing bytes***************")
    for i in byte_all_content:
        if i[0] in executed_set:
            pass
        else:
            print(i)
        f = open("analyse_result.txt", "a+")
    print("*******************************************\n")

    result = ""
    print("executable bytes: " + str(byte_all))
    print("executed bytes: " + str(executed_count))
    byte_ratio = float(executed_count)/byte_all*100
    print("byte coverage: " + str(byte_ratio) + "%")

    result += "executable bytes: " + str(byte_all) + "\n"
    result += "executed bytes: " + str(executed_count) + "\n"
    result += "byte coverage: " + str(byte_ratio) + "%" + "\n"
    result += "\n\n"

    # 读取函数覆盖率、语句覆盖率、分支覆盖率信息
    oldcontent = f.readlines()
    index = [3, 4, 8, 9, 14, 15]
    valuecontent = []
    for i in index:
        tmp = oldcontent[i]
        tmp = tmp.split(":")[-1]
        tmp = tmp.strip()
        tmp = int(tmp)
        valuecontent.append(tmp)
    executable = valuecontent[0] + valuecontent[1] + valuecontent[2] + valuecontent[4] + byte_all
    executed = valuecontent[0] + valuecontent[3] + valuecontent[4] - valuecontent[5] + executed_count
    # 统计综合的覆盖率
    all_ratio = float(executed)/executable * 100
    result += "all coverage: " + str(all_ratio) + "%"

    # 将所有信息重新写入文件
    f.write(result)
    f.close()
    print("\nanalyse_result.txt is created to store analysis result.")

    # 删除修改过的pyc文件
    if os.path.exists(pyc_file_name):
        os.remove(pyc_file_name)


