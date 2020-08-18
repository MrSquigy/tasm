"""Tasm is the assembly language for toy-machine."""

import argparse
from sys import exit
from typing import Callable, Final
import os

parser = argparse.ArgumentParser(description="Assemble tasm files for toy-machine.")
parser.add_argument("source", type=str, help="Source tasm file", nargs=1)
parser.add_argument(
    "-o", type=str, dest="output", help="Name of the output file", nargs=1,
)

register_reference: Final[dict[str, int]] = {
    "AC": 0,
    "DR": 1,
    "CR": 2,
    "PC": 3,
    "IR": 4,
}

find_register = lambda name: format(register_reference[name], "03b")
find_memory = lambda addr, bits: format(int(addr, 16), f"0{bits}b")
make_const = lambda val, bits: format(int(val), f"0{bits}b")
tense = lambda num: "were" if num > 1 or num <= 0 else "was"


def check_args(instr: str, args: list[str], required: int) -> None:
    if (l := len(args)) != required:
        raise SyntaxError(
            f"{instr} instruction requires {required} arguments, but {l} {tense(l)} supplied."
        )


def add(args: list[str]) -> str:
    check_args("add", args, required=2)
    code = "0b0001"

    if args[0].upper() in register_reference:
        reg = find_register(args[0].upper())
        if args[1].isnumeric():
            # add_reg_const
            code += "01"
            code += reg
            code += make_const(args[1], 23)
        elif "x" in args[1]:
            # add_reg_mem
            code += "10"
            code += reg
            code += find_memory(args[1], 23)
        else:
            raise SyntaxError(
                "add instruction can only add a constant value or a value from memory when storing in a register."
            )
    elif "x" in args[0]:
        if args[1].upper() in register_reference:
            # add_mem_reg
            code += "11"
            code += find_memory(args[0], 23)
            code += find_register(args[1].upper())
        else:
            raise SyntaxError(
                "add instruction can only add a value from a register when storing in a memory location."
            )
    else:
        raise SyntaxError(
            "add instruction requires a register or memory location as the first argument."
        )

    return code


def move(args: list[str]) -> str:
    check_args("move", args, required=2)
    code = "0b000"

    if args[0].upper() in register_reference:
        reg = find_register(args[0].upper())
        if args[1].isnumeric():
            # move_reg_const
            code += "000"
            code += reg
            code += make_const(args[1], 23)
        elif "x" in args[1]:
            # move_reg_mem
            code += "001"
            code += reg
            code += find_memory(args[1], 23)
        else:
            raise SyntaxError(
                "move instruction only allows to store a constant value or a value from memory in a register."
            )
    elif "x" in args[0]:
        if args[1].isnumeric():
            # move_mem_const
            code += "010"
            code += find_memory(args[0], 10)
            code += make_const(args[1], 16)
        elif "x" in args[1]:
            # move_mem_mem
            code += "011"
            code += find_memory(args[0], 13)
            code += find_memory(args[1], 13)
        elif args[1].upper() in register_reference:
            # move_mem_reg
            code += "100"
            code += find_memory(args[0], 23)
            code += find_register(args[1].upper())
        else:
            raise SyntaxError(
                "move instruction only allows to store: a constant value; a value from memory; or a value from a register, in memory."
            )
    else:
        raise SyntaxError(
            "move instruction requires a register or memory location as the first parameter."
        )

    return code


instruction_reference: dict[str, Callable[[list[str]], str]] = {
    "add": add,
    "mov": move,
}

args = parser.parse_args()
source_name = args.source[0]
output_name = args.output[0] if args.output is not None else source_name[:-5]
output_name = os.path.join("build", output_name)
human_name = output_name.split(os.path.sep)[-1]
source: list[str]
program_code: list[str] = []

if not (os.path.exists("build") and os.path.isdir("build")):
    os.mkdir("build")

with open(source_name) as source_file:
    source = source_file.read().split("\n")

for i, line in enumerate(source):
    tokens = line.replace(",", "").split()

    if tokens[0] not in instruction_reference:
        print(f"Error on line {i + 1}: {tokens[0]} is not a tasm instruction")
        exit()

    try:
        code = instruction_reference[tokens[0]](tokens[1:])
        program_code.append(code + "\n")
    except SyntaxError as e:
        print(f"Error on line {i + 1}: {e}")
        exit()


with open(output_name, "w") as output_file:
    output_file.writelines(program_code)

print(f"Successfully assembled `{source_name}` as `{human_name}` in the `build` dir")
