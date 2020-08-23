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

WORD_SIZE: Final[int] = 32
MEM_ADDR_BITS: Final[int] = 10

register_reference: Final[dict[str, int]] = {
    "AC": 0,
    "DR": 1,
    "CR": 2,
    "PC": 3,
    "IR": 4,
}

tense = lambda num: "were" if num > 1 or num <= 0 else "was"


def fmt_const(data: str) -> str:
    c = bin(int(data))[2:]
    if (l := len(c)) > WORD_SIZE:
        raise SyntaxError(
            f"maximum data size is {WORD_SIZE} bits, however {data} requires {l} bits."
        )

    return c


def fmt_mem(addr: str) -> str:
    addr_i = int(addr, 16)
    if addr_i >= (a := 2 ** MEM_ADDR_BITS):
        raise SyntaxError(
            f"maximum memory address is {a - 1}, however address {addr_i} is referenced."
        )

    return format(addr_i, f"0{MEM_ADDR_BITS}b")


def fmt_reg(register: str) -> str:
    return format(register_reference[register], "03b")


def check_args(instr: str, args: list[str], required: int) -> None:
    if (l := len(args)) != required:
        raise SyntaxError(
            f"{instr} instruction requires {required} arguments, but {l} {tense(l)} supplied."
        )


def assemble_instruction(opcode: str, first_param: str, second_param: str) -> str:
    code = opcode + first_param

    extra_bits = len(opcode) + len(first_param) + len(second_param) - WORD_SIZE - 2
    if extra_bits > 0:
        code = "0b111111" + first_param  # Multiline reserved opcode
        code += second_param[:-extra_bits]
        padded_bits = WORD_SIZE - len(opcode) - extra_bits + 2
        remainder = "0" * padded_bits + second_param[-extra_bits:]
        code += "\n" + opcode + remainder
    elif extra_bits < 0:
        code += "0" * (extra_bits * -1) + second_param
    else:
        code += second_param

    return code


def add(args: list[str]) -> str:
    check_args("add", args, required=2)
    code: str

    if args[0].upper() in register_reference:
        reg = fmt_reg(args[0].upper())
        if args[1].isnumeric():
            # add_reg_const
            code = "0b000101"
            code = assemble_instruction(code, reg, fmt_const(args[1]))
        elif "x" in args[1]:
            # add_reg_mem
            code = "0b000110"
            code = assemble_instruction(code, reg, fmt_mem(args[1]))
        else:
            raise SyntaxError(
                "add instruction can only add a constant value or a value from memory when storing in a register."
            )
    elif "x" in args[0]:
        if args[1].upper() in register_reference:
            # add_mem_reg
            code = "0b000111"
            reg = fmt_reg(args[1].upper())
            code = assemble_instruction(code, fmt_mem(args[0]), reg)
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
    code: str

    if args[0].upper() in register_reference:
        reg = fmt_reg(args[0].upper())
        if args[1].isnumeric():
            # move_reg_const
            code = "0b000000"
            code = assemble_instruction(code, reg, fmt_const(args[1]))
        elif "x" in args[1]:
            # move_reg_mem
            code = "0b000001"
            code = assemble_instruction(code, reg, fmt_mem(args[1]))
        else:
            raise SyntaxError(
                "move instruction only allows to store a constant value or a value from memory in a register."
            )
    elif "x" in args[0]:
        if args[1].isnumeric():
            # move_mem_const
            code = "0b000010"
            code = assemble_instruction(code, fmt_mem(args[0]), fmt_const(args[1]))
        elif "x" in args[1]:
            # move_mem_mem
            code = "0b000011"
            code = assemble_instruction(code, fmt_mem(args[0]), fmt_mem(args[1]))
        elif args[1].upper() in register_reference:
            # move_mem_reg
            code = "0b000100"
            code = assemble_instruction(
                code, fmt_mem(args[0]), fmt_reg(args[1].upper())
            )
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
