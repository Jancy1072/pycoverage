# encoding: utf-8
import sys
import os
import linecache
import re

# 获取命令行参数
trace_file = sys.argv[1]
# 判断文件是否存在
if os.path.exists(trace_file):
    pass
else:
    print("File is not found.")
    sys.exit(1)

# 获取测试文件的绝对路径
file_abspath = os.path.abspath(trace_file)
# 获取测试文件的pyc文件的绝对路径
pyc_file = file_abspath + "c"
# 判断文件是否存在
if os.path.exists(pyc_file):
    os.remove(pyc_file)
# 所有函数
call_all = []
# 调用的函数
call_lines = []
# 执行的行
executed_lines = []
# 执行的分支
executed_pairs = []
# 分支标记
pre_no = 0
# 存储所有要写入文件的字符串
result = ""

# 自定义的追踪函数
def my_trace_call(frame, event, arg):
    global file_abspath
    global call_all
    global call_lines
    global executed_lines
    global executed_pairs
    global pre_no
    global result

    # call事件触发
    if event == 'call':
        code = frame.f_code # 字节码
        file_name = code.co_filename # 所在文件名

        if file_name == file_abspath:
            function_name = code.co_name # 函数名
            line_no = frame.f_lineno # 行号

            caller = frame.f_back # 调用者
            caller_function_name = caller.f_code.co_name # 调用者所在函数名
            caller_file_name = caller.f_code.co_filename # 调用者所在文件

            caller_line_no = caller.f_lineno # 调用者的行号

            call_lines.append((caller_file_name, caller_function_name, function_name))

    # line事件触发
    elif event == 'line':
        code = frame.f_code # 字节码
        file_name = code.co_filename # 所在文件名

        if file_name == file_abspath:
            function_name = code.co_name # 所在函数名
            line_no = frame.f_lineno # 行号

            statement = linecache.getline(file_name, line_no) # 行号对应的语句
            prestatement = linecache.getline(file_name, pre_no) # 前一个语句

            # 词法分析，是否为关键字def、if、elif、for、while
            statement_parts = re.split("\s|\(|\,|\)|\:", statement)
            prestatement_parts = re.split("\s|\(|\,|\)|\:", prestatement)

            for word in statement_parts:
                if "def" == word:
                    a = re.sub(r'def\s*', "", statement)
                    b = re.sub(r'\(.*\):\n', "", a)
                    call_all.append(b) # 保存所有函数
                    break

            for word in prestatement_parts:
                if "if" == word or "elif" == word or "for" == word or "while" == word:
                    if pre_no != -1:
                        executed_pairs.append((pre_no, line_no)) # 保存执行过的分支
                    break

            executed_lines.append(line_no) # 保存执行过的行号
            pre_no = line_no # 前一个行号
            print("line %d: %s" % (line_no, statement.rstrip()))
            result += "line " + str(line_no) + ": " + statement.rstrip() + "\n"

    # return事件触发
    elif event == 'return':
        code = frame.f_code # 字节码
        file_name = code.co_filename # 所在文件名

        if file_name == file_abspath:

            function_name = code.co_name # 函数名
            line_no = frame.f_lineno # 行号

            statement = linecache.getline(file_name, line_no) # 行号对应的语句
            # 词法分析，是否为关键字if、elif、for、while
            statement_parts = re.split("\s|\(|\,|\)|\:", statement)
            for word in statement_parts:
                if "if" == word or "elif" == word or "for" == word or "while" == word:
                    executed_pairs.append((line_no, -1))
                    pre_no = -1 # 设置标记为-1
                    break

    return my_trace_call


sys.settrace(my_trace_call) # 监听自定义追踪函数

print("\n*****************Trace lines*****************")
__import__(trace_file.replace(".py", ""))
print("*********************************************\n")

# 将中间结果写入coverage.txt文件
f = open("coverage.txt", "w+")

f.writelines(file_abspath)
f.writelines("\n")
f.writelines(",".join(i for i in call_all))
f.writelines("\n")
f.writelines(";".join(str(i[1:]) for i in call_lines[1:]))
f.writelines("\n")
f.writelines(",".join(str(i) for i in executed_lines))
f.writelines("\n")
f.writelines(";".join(str(i) for i in executed_pairs))
f.close()

print("\ncoverage.txt is created to store important statistic result.")

# 将执行的路径信息/行信息写入trace_result.txt
f = open("trace_result.txt", "w+")
f.write(result)
f.close()

print("\ntrace_result.txt is created to store trace lines.")