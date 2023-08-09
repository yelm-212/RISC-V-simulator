import sys
from enum import Enum
# COMP0411
# 2019116962 Yerim shin


# Processor's clock cycle (global clock)
cpu_cycles = 0
END = int('0xDEADBEEF', 16)

'''
 Processor's States:
   (1) Register (x32)
   (2) Program Counter
   (3) Data Memory
   (4) Instruction Memory
'''

REGS_SIZE = 32
IMEM_SIZE = 32 * 1024  # 4 KiB of instruction memory (I$)
DMEM_SIZE = 32 * 1024  # 4 KiB of data memory (D$)

reg = [0 for _ in range(REGS_SIZE)]  # (1) -> 32 (general-purpose) registers
PC = 0  # (2) -> Let's assume that program segment starts from 0x00000000
inst_mem = [0 for _ in range(IMEM_SIZE)]
data_mem = [0 for _ in range(DMEM_SIZE)]

DMEM_flag = [False for _ in range(DMEM_SIZE)]  # a set of flags for checking the data memory == touched or not
'''
  Tip: Data types
    (i) long = 4 bytes = 32 bits
    (ii) long long int = 8 bytes = 64 bits
'''

opcodes = dict(I=['0000011', '0001111', '0010011', '0011011', '1100111', '1110011'],
               R='0110011',
               U=['0010111', '0110111'],
               S='0100011',
               B='1100011',
               UJ='1101111')


class BranchComp():
    def __init__(self):
        self.BrEq = None
        self.BrLT = None
        self.BrOp = self.Br_Vals.init

    # TODO : implement Branch Operations
    def setBr(self, A, B):
        if A == B:
            self.BrEq = 1
        else:
            self.BrEq = 0

        if A < B:
            self.BrLT = 1
        else:
            self.BrLT = 0

    class Br_Vals(Enum):
        init = None
        beq = 0
        bne = 1
        blt = 2
        bltu = 3
        bgeu = 4
        bge = 5


class Control_Unit():
    def __init__(self):
        self.MemRw = None
        self.ImmSel = self.ImmSel_Vals(None)
        self.ALUSel = self.ALUSel_Vals(None)
        self.RegWEn = 0
        # 0 means disabled to write,
        # 1 means able to write
        self.BrUN = 0
        # Unsigned bit
        self.ASel = 0  # 0 for reg. val, 1 for immediate val.
        self.BSel = 0  # 0 for reg. val, 1 for immediate val.
        self.WBSel = self.WBSel_Vals.dont
        # dont care 안쓰는 방법은 없는지 생각해보기
        self.PCSel = self.PCSel_vals.not_taken

    def setFlags(self, inst):
        if inst[-7:] in opcodes.get("R"):
            self.ImmSel = self.ImmSel_Vals.R
        if inst[-7:] in opcodes.get("I"):
            self.ImmSel = self.ImmSel_Vals.I
        if inst[-7:] in opcodes.get("U"):
            self.ImmSel = self.ImmSel_Vals.U
        if inst[-7:] in opcodes.get("S"):
            self.ImmSel = self.ImmSel_Vals.S
        if inst[-7:] in opcodes.get("B"):
            self.ImmSel = self.ImmSel_Vals.B
        if inst[-7:] in opcodes.get("UJ"):
            self.ImmSel = self.ImmSel_Vals.UJ

    def setALUSel(self, inst):
        if inst[-7:] == opcodes.get("R"):
            self.ASel = 0
            self.BSel = 0
            self.RegWEn = 1
            self.BrUN = 0
            self.MemRw = None  # dont care
            self.WBSel = self.WBSel_Vals.alu
            self.PCSel = self.PCSel_vals.not_taken

            if inst[-15:-12] == "000" and inst[-32:-25] == "0000000":
                self.ALUSel = self.ALUSel_Vals.ADD
            elif inst[-15:-12] == "000" and inst[-32:-25] == "0100000":
                self.ALUSel = self.ALUSel_Vals.SUB
            elif inst[-15:-12] == "001" and inst[-32:-25] == "0000000":
                self.ALUSel = self.ALUSel_Vals.SLL
            elif inst[-15:-12] == "010" and inst[-32:-25] == "0000000":
                self.ALUSel = self.ALUSel_Vals.MUL
            elif inst[-15:-12] == "011" and inst[-32:-25] == "0000000":
                self.ALUSel = self.ALUSel_Vals.DIV
            elif inst[-15:-12] == "100" and inst[-32:-25] == "0000000":
                self.ALUSel = self.ALUSel_Vals.XOR
            elif inst[-15:-12] == "101" and inst[-32:-25] == "0000000":
                self.ALUSel = self.ALUSel_Vals.SRL
            elif inst[-15:-12] == "101" and inst[-32:-25] == "0100000":
                self.ALUSel = self.ALUSel_Vals.REM
            elif inst[-15:-12] == "110" and inst[-32:-25] == "0000000":
                self.ALUSel = self.ALUSel_Vals.OR
            elif inst[-15:-12] == "111" and inst[-32:-25] == "0000000":
                self.ALUSel = self.ALUSel_Vals.AND

        if inst[-7:] == opcodes.get("I")[0]:  # Load Instructions
            self.ALUSel = self.ALUSel_Vals.ADD
            self.MemRw = self.MemRw_Vals.Read

            if inst[-15:-13] == "010":  # lw
                self.ASel = 0
                self.BSel = 1
                self.RegWEn = 1
                self.BrUN = 0
                self.WBSel = self.WBSel_Vals.mem
                self.PCSel = self.PCSel_vals.not_taken

        if inst[-7:] == opcodes.get("S"):  # Store Instructions
            self.ALUSel = self.ALUSel_Vals.ADD

            if inst[-15:-13] == "010":  # sw
                self.ASel = 0
                self.BSel = 1
                self.RegWEn = 0
                self.BrUN = 0
                self.MemRw = self.MemRw_Vals.Write
                self.WBSel = self.WBSel_Vals.dont
                self.PCSel = self.PCSel_vals.not_taken

        if inst[-7:] == opcodes.get("I")[1]:  # Fence Instructions
            pass

        if inst[-7:] == opcodes.get("I")[2]:
            self.ASel = 0
            self.BSel = 1
            self.RegWEn = 1
            self.BrUN = 0
            self.MemRw = None
            self.WBSel = self.WBSel_Vals.alu
            self.PCSel = self.PCSel_vals.not_taken
            if inst[-15:-12] == "000":
                self.ALUSel = self.ALUSel_Vals.ADD
            elif inst[-15:-12] == "001" and inst[-32:-24] == "0000000":
                self.ALUSel = self.ALUSel_Vals.SLL
            elif inst[-15:-12] == "010":
                self.ALUSel = self.ALUSel_Vals.MUL
            elif inst[-15:-12] == "011":
                self.ALUSel = self.ALUSel_Vals.DIV
            elif inst[-15:-12] == "100":
                self.ALUSel = self.ALUSel_Vals.XOR
            elif inst[-15:-12] == "101" and inst[-32:-24] == "0000000":
                self.ALUSel = self.ALUSel_Vals.SRL
            elif inst[-15:-12] == "101" and inst[-32:-24] == "0100000":
                self.ALUSel = self.ALUSel_Vals.REM
            elif inst[-15:-12] == "110":
                self.ALUSel = self.ALUSel_Vals.OR
            elif inst[-15:-12] == "111":
                self.ALUSel = self.ALUSel_Vals.AND

        if inst[-7:] == opcodes.get("I")[4]:  # jalr
            self.ALUSel = self.ALUSel_Vals.ADD
            self.ASel = 0
            self.BSel = 1
            self.RegWEn = 1
            self.BrUN = 0
            self.WBSel = self.WBSel_Vals.nextPC
            self.PCSel = self.PCSel_vals.taken
            self.MemRw = self.MemRw_Vals.Read

        if inst[-7:] == opcodes.get("B"):
            self.ASel = 1
            self.BSel = 1
            self.RegWEn = 0
            self.BrUN = 0
            self.ALUSel = self.ALUSel_Vals.ADD
            self.WBSel = self.WBSel_Vals.dont
            self.MemRw = self.MemRw_Vals.Read
            self.PCSel = self.PCSel_vals.not_taken
            # PCSel will be computed at EXE stage

            if inst[-15:-12] == "000":
                BC.BrOp = BC.Br_Vals.beq
            elif inst[-15:-12] == "100":
                BC.BrOp = BC.Br_Vals.blt
            elif inst[-15:-12] == "101":
                BC.BrOp = BC.Br_Vals.bge
            elif inst[-15:-12] == "110":
                BC.BrOp = BC.Br_Vals.bltu
                self.BrUN = 1
            elif inst[-15:-12] == "111":
                BC.BrOp = BC.Br_Vals.bgeu
                self.BrUN = 1

        if inst[-7:] == opcodes.get("U")[0]:  # auipc
            self.ALUSel = self.ALUSel_Vals.ADD
            self.ASel = 1
            self.BSel = 1
            self.RegWEn = 1
            self.BrUN = 0
            self.WBSel = self.WBSel_Vals.alu
            self.PCSel = self.PCSel_vals.not_taken
            self.MemRw = self.MemRw_Vals.Read

        if inst[-7:] == opcodes.get("U")[1]:  # lui
            self.ALUSel = self.ALUSel_Vals.B
            self.MemRw = self.MemRw_Vals.Read
            self.ASel = None
            self.BSel = 1
            self.RegWEn = 1
            self.BrUN = 0
            self.WBSel = self.WBSel_Vals.alu
            self.PCSel = self.PCSel_vals.not_taken

        if inst[-7:] == opcodes.get("UJ"):  # jal
            self.ALUSel = self.ALUSel_Vals.ADD
            self.ASel = 1
            self.BSel = 1
            self.RegWEn = 1
            self.BrUN = 0

            self.WBSel = self.WBSel_Vals.nextPC
            self.PCSel = self.PCSel_vals.taken
            self.MemRw = self.MemRw_Vals.Read

    class ImmSel_Vals(Enum):
        n = None  # init val. for ImmSel
        R = 1
        I = 2
        U = 3
        S = 4
        B = 5
        UJ = 6

    class ALUSel_Vals(Enum):
        B = 10
        n = None  # init val.
        ADD = 0
        SUB = 1
        XOR = 2
        AND = 3
        OR = 4
        SLL = 5
        SRL = 6
        MUL = 7
        DIV = 8
        REM = 9

    class MemRw_Vals(Enum):
        Read = 0
        Write = 1

    class WBSel_Vals(Enum):
        mem = 0
        alu = 1
        nextPC = 2
        dont = 3

    class PCSel_vals(Enum):
        not_taken = 0
        taken = 1


'''
  Functions for modelling 5-stages with 1 control unit
    (1) IF: Fetching instructions from instruction memory
    (2) ID: Decoding instructions (also access registers)
    (3) EX: Executing (ALU)
    (4) MEM: Accessing to data memory
    (5) WB: Write-back (store result data to a target register)
    (6) Control Unit

    * return type of IF, ID, EX, MEM, WB, Control_Unit function should not be changed.
'''


# TODO: your work should be done with completing these five + addtional helper functions:

def IF(PC):
    inst = bin(inst_mem[PC // 4])[2:]
    return "0" * (32 - len(inst)) + inst

def ID(inst):
    # Decodes instructions (also access registers)
    # and Immediate Gengeration
    global Imm, rd, R1, R2


    CU.setFlags(inst)
    CU.setALUSel(inst)
    newImm = list("0"*32)
    # TODO : implement accessing register vals and immediate gen.
    if CU.ImmSel == CU.ImmSel_Vals.R:
        rs1 = int('0b'+inst[-20:-15], 2)
        rs2 = int('0b'+inst[-25:-20], 2)
        rd = int('0b'+inst[-12:-7], 2)
        R1 = reg[rs1]
        R2 = reg[rs2]
    if CU.ImmSel == CU.ImmSel_Vals.I:
        rs1 = int('0b'+inst[-20:-15], 2)
        newImm = inst[0] * 20 + inst[0:12]
        Imm = ''.join(newImm)
        rd = int('0b' + inst[-12:-7], 2) # ok
        R1 = reg[rs1] # ok
    if CU.ImmSel == CU.ImmSel_Vals.S:
        rs1 = int('0b'+inst[-20:-16], 2)
        rs2 = int('0b'+inst[-25:-20], 2)
        newImm = str(inst[0]) * 20 + str(inst[-32:-25]) + str(inst[-12:-7])
        Imm = ''.join(newImm)
        R1, R2 = reg[rs1], reg[rs2]
    if CU.ImmSel == CU.ImmSel_Vals.U:
        newImm = str(inst[-32:-12]) + "0"*12
        Imm = newImm
        rd = int('0b'+inst[-12:-7], 2)
    if CU.ImmSel == CU.ImmSel_Vals.B:
        rs1 = int('0b'+inst[-20:-15], 2) # ㅇㅋ
        rs2 = int('0b'+inst[-25:-20], 2) # ㅇㅋ
        R1 = reg[rs1]
        R2 = reg[rs2]
        newImm = str(inst[0]) * 20 + str(inst[-8]) + str(inst[-31:-25]) + str(inst[-12:-8]) + "0"
        Imm = ''.join(newImm)
    if CU.ImmSel == CU.ImmSel_Vals.UJ:
        newImm = str(inst[0]) * 12 + str(inst[-21:-13]) + str(inst[-21]) + str(inst[-32:-22]) + "0"
        Imm = ''.join(newImm)
        rd = int('0b'+inst[-12:-7], 2)


def EX():
    # CU.ASel, CU.BSel, CU.ALUSel
    if CU.ASel == 0:
        A = R1
    elif CU.ASel == 1:
        A = PC

    if CU.BSel == 0:
        B = R2
    elif CU.BSel == 1:
        B = int('0b'+Imm, 2)

    # TODO : implement Branch Operations
    # 무한루프 오류 수정
    if CU.ImmSel == CU.ImmSel_Vals.B:
        BC.setBr(R1, R2)
        if BC.BrOp == BC.Br_Vals.beq:
            if BC.BrEq == 1:
                CU.PCSel = CU.PCSel_vals.taken
        if BC.BrOp == BC.Br_Vals.bne:
            if BC.BrEq == 0:
                CU.PCSel = CU.PCSel_vals.taken
        if BC.BrOp == BC.Br_Vals.blt:
            if BC.BrLT == 1:
                CU.PCSel = CU.PCSel_vals.taken
        if BC.BrOp == BC.Br_Vals.bge:
            if BC.BrLT == 0:
                CU.PCSel = CU.PCSel_vals.taken
        if BC.BrOp == BC.Br_Vals.bltu:
            if BC.BrLT == 1:
                CU.PCSel = CU.PCSel_vals.taken
        if BC.BrOp == BC.Br_Vals.bgeu:
            if BC.BrLT == 0:
                CU.PCSel = CU.PCSel_vals.taken

    res = 0
    # TODO : implement accurate 32-bit operation result
    if CU.ALUSel == CU.ALUSel.ADD:
        res = A + B
    elif CU.ALUSel == CU.ALUSel.SUB:
        res = A - B
    elif CU.ALUSel == CU.ALUSel.OR:
        res = A | B
    elif CU.ALUSel == CU.ALUSel.XOR:
        res = A ^ B
    elif CU.ALUSel == CU.ALUSel.AND:
        res = A & B
    elif CU.ALUSel == CU.ALUSel.MUL:
        res = A * B
    elif CU.ALUSel == CU.ALUSel.DIV:
        res = A // B
    elif CU.ALUSel == CU.ALUSel.REM:
        res = A % B
    elif CU.ALUSel == CU.ALUSel.B:
        res = B

    return res % int('0x100000000', 16) # 결과는 32bit hexadecimal


def MEM():
    if CU.MemRw == CU.MemRw_Vals.Read:
        return
        # return data_mem[alu]
    elif CU.MemRw == CU.MemRw_Vals.Write:
        data_mem[alu] = R2
        DMEM_flag[alu] = True
        return data_mem[alu]
    else:
        return None


def WB():
    if CU.WBSel == CU.WBSel.dont:
        return

    if CU.RegWEn == 1:
        if CU.WBSel == CU.WBSel.mem:
            reg[rd] = mem
        elif CU.WBSel == CU.WBSel.alu:
            reg[rd] = alu
        elif CU.WBSel == CU.WBSel.nextPC:
            reg[rd] = PC + 4

def init_states(_binary_exe):
    global PC
    """
		Initializing instruction memory
		- Copying all instructions from a given binary executable file
		- One element in inst_mem[] contains one line of RV32I's instruction
	"""
    cnt = 0
    for line in _binary_exe:
        inst_mem[cnt] = int('0b' + line[:-1], 2)  # str binary representation to interger
        cnt += 1

    PC = 0  # -> Let's assume that program segment starts from 0x00000000


def print_statistics():
    print("Processor's clock cycles: ", cpu_cycles)


def dump_registers():
    print(">>>>>>>>[REGISTER DUMP]<<<<<<<")
    print("PC = ", PC)
    n = 0
    for r in reg:
        print('x' + str(n) + " = ", r);
        n += 1
    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")


def dump_memory():
    print(">>>>>>>>[MEMORY DUMP]<<<<<<<<<")
    for i in range(DMEM_SIZE):
        if DMEM_flag[i]:
            print(i, ':', data_mem[i])
    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")


halt = False
idx = 0

_exe = open(sys.argv[1], 'r')
init_states(_exe)

CU = Control_Unit() # new control unit class
BC = BranchComp() # new Branch composition unit

while not halt:
    inst = IF(PC)
    Imm = '0' * 32  # initialized as binary string except 0b
    rd, R1, R2 = None, None, None #
    ID(inst)
    alu = EX()
    mem = MEM()
    WB()
    if CU.PCSel == CU.PCSel_vals.not_taken:
        PC = PC + 4
    elif CU.PCSel == CU.PCSel_vals.taken:
        PC = alu
    """
		Exit condition: when the value of 31st register == 0xDEADBEEF, then stop the simulation.
					(End of the program)
	"""
    if reg[31] == END:
        halt = True

    cpu_cycles += 1

print_statistics()  # print processor's clock cycles
dump_registers()  # print all contents of registers
dump_memory()  # print all used data in (data) memory
