
from sys import argv
from TaskDef import TaskGroup, Task

if len(argv) == 2:
    TaskGroup(argv[1]).run()
else:
    while True:
        row = input("Command: ")
        Task(row).run()
        print()