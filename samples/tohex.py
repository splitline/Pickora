import sys

print("Input some integers (seperate with semicolon `;`):")
line = sys.stdin.readline()

input_list = map(str.strip, line.split(":"))
hex_res = map(hex, map(int, input_list))
print("Result:", ",".join(hex_res))
