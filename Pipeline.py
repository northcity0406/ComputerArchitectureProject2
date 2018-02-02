##On my honor, I have neither given nor received unauthorized aid on this assignment
import sys
class PipeLine:
    def __init__(self):
        self.instruction = {
            '010000': 'J',
            '010001': 'JR',
            '010010': 'BEQ',
            '010011': 'BLTZ',
            '010100': 'BGTZ',
            '010101': 'BREAK',
            '010110': 'SW',
            '010111': 'LW',
            '011000': 'SLL',
            '011001': 'SRL',
            '011010': 'SRA',
            '011011': 'NOP',

            '110000': 'ADD',
            '110001': 'SUB',
            '110010': 'MUL',
            '110011': 'AND',
            '110100': 'OR',
            '110101': 'XOR',
            '110110': 'NOR',
            '110111': 'SLT',
            '111000': 'ADDI',
            '111001': 'ANDI',
            '111010': 'ORI',
            '111011': 'XORI',
        }
        self.Rdata = [0] * 32
        self.Memory_Data = []
        self.Real_code = {}
        self.Code = {}
        self.Data_start = 0
        self.Data_end = 0
        self.max_R = 32

        self.waiting = 0
        self.executed = 0
        self.preIssue = []
        self.preAlu1 = []
        self.preMem = []
        self.postMem = []
        self.preAlu2 = []
        self.postAlu2 = []
        self.readLock = [False] * 33
        self.canStore = True
        self.read = [4] * 33
        self.write = [4] * 33

        self.cycle = 1
        self.PC = 256
        self.JumpBreak = False
        self.offset = 0
        self.isBreak = False

    def Complement(self, a):
        if a != "" and a[0] == '0':
            return int(a, 2)
        if a != "" and a[0] == '1':
            return -(~int(a[1:], 2) + 1) - 2147483648

    def Register_Memory(self, Qpcode, instruct):
        if Qpcode in ['ADD', 'SUB', 'MUL', 'AND', 'OR', 'XOR', 'NOR', 'SLT']:  ##ADD rd,rs,rt
            x = instruct[16:21]  ##rd
            y = instruct[6:11]  ##rs
            z = instruct[11:16]  ##rt
            t = ' R%d, R%d, R%d' % (int(x, 2), int(y, 2), int(z, 2))
            s = [int(x, 2), int(y, 2), int(z, 2)]
            return [s, t]
        elif Qpcode in ['ADDI', 'ANDI', 'ORI', 'XORI']:  ##ADD rd,rs,rt
            x = instruct[16:]  ##immediate value
            y = instruct[6:11]  ##rs
            z = instruct[11:16]  ##rt
            t = ' R%d, R%d, #%d' % (int(z, 2), int(y, 2), int(x, 2))
            s = [int(z, 2), int(y, 2), int(x, 2)]
            return [s, t]
        elif Qpcode == 'J':  ##在256M的空间内跳动
            tmp = instruct[6:] + '00'
            t = ' #%d' % (int(tmp, 2))
            s = [int(tmp, 2)]
            return [s, t]
        ##JR待改进，tmp = instruct[6:11]可能不正确
        ##JR跳到寄存器tmp
        elif Qpcode == 'JR':
            tmp = instruct[6:11]
            t = ' R%d' % (int(tmp, 2))
            s = [int(tmp, 2)]
            return [s, t]
        elif Qpcode == 'BEQ':
            x = instruct[16:] + '00'  ##offset
            y = instruct[6:11]  ##rs
            z = instruct[11:16]  ##rt
            t = ' R%d, R%d, #%d' % (int(y, 2), int(z, 2), int(x, 2))
            s = [int(y, 2), int(z, 2), int(x, 2)]
            return [s, t]
        elif Qpcode in ['BLTZ', 'BGTZ']:
            x = instruct[16:] + '00'  ##offset
            y = instruct[6:11]  ##rs
            # z = instruct[11:16]  ##rt  //rt使用不到
            t = ' R%d, #%d' % (int(y, 2), int(x, 2))
            s = [int(y, 2), int(x, 2)]
            return [s, t]
        elif Qpcode in ['BREAK', 'NOP']:
            s = []
            t = ""
            return [s, t]
        elif Qpcode in ['LW', 'SW']:
            x = instruct[16:]  ##offset
            y = instruct[6:11]  ##rs
            z = instruct[11:16]  ##rt
            t = ' R%d, %d(R%d)' % (int(z, 2), int(x, 2), int(y, 2))
            s = [int(z, 2), int(x, 2), int(y, 2)]
            return [s, t]
        elif Qpcode in ['SLL', 'SRA', 'SRL']:
            x = instruct[21:26]  ##offset
            y = instruct[16:21]  ##rd
            z = instruct[11:16]  ##rt
            t = ' R%d, R%d, #%d' % (int(y, 2), int(z, 2), int(x, 2))
            s = [int(y, 2), int(z, 2), int(x, 2)]
            return [s, t]

    def Translate(self,h):
        f = h
        g = open('disassembly.txt', 'w')
        index = 256
        Flag = True
        for each in f.readlines():
            each = each.replace('\n', '')
            tmp = each[0:6]
            if Flag == True:
                tmp_instruction = self.instruction[tmp]
                if tmp_instruction == 'BREAK':
                    self.Data_start = index + 4
                    Flag = False
                tmp_Register_Memory = self.Register_Memory(self.instruction[tmp], each)
                self.Real_code[index] = [tmp_instruction, tmp_Register_Memory[0]]
                self.Code[index] = "%s%s" % (tmp_instruction, tmp_Register_Memory[1])
                g.write("%s\t%d\t%s%s\n" % (each, index, tmp_instruction, tmp_Register_Memory[1]))
            else:
                data = self.Complement(each)
                self.Memory_Data.append(data)
                g.write("%s\t%d\t%s\n" % (each, index, data))
                self.Data_end = index
            index += 4

    def Jump(self, PC):
        '''
        返回值：BOOL
        True:可以执行分支，更新PC
        False:不可以执行分支
        '''
        # print(PC)
        instruct = self.Real_code[PC]
        # print(instruct)
        self.JumpBreak = True
        if instruct[0] == 'J':  # 字典:{292: ['J', [264]]}  292: J #264
            self.PC = int(instruct[1][0])
            # print(self.PC)
            self.JumpBreak = False
            return True
        elif instruct[0] == 'JR':  # 字典:{284: ['JR', [2]]}   284: JR R2
            self.PC = self.Rdata[int(instruct[1][0])]
            self.JumpBreak = False
            return True
        elif instruct[0] == 'BEQ':  # 字典:{264: ['BEQ', [1, 2, 28]]}  264: BEQ R1, R2, #28
            r1 = int(instruct[1][0])
            r2 = int(instruct[1][1])
            offset = int(instruct[1][2])
            if self.readLock[r1] == False and self.readLock[r2] == False:  ##读取的两个寄存器都没有RAW
                if self.Rdata[r1] == self.Rdata[r2]:
                    self.PC += offset + 4
                else:
                    self.PC += 4
                self.JumpBreak = False
                return True
            else:
                return False
        elif instruct[0] == "BLTZ":  # 字典:{260: ['BLTZ', [1, 28]]}  264: BLTZ R1, #28
            r1 = int(instruct[1][0])
            offset = int(instruct[1][1])
            if self.readLock[r1] == False:  ##读取的寄存器没有RAW
                if self.Rdata[r1] < 0:
                    self.PC += offset + 4
                else:
                    self.PC += 4
                self.JumpBreak = False
                return True
            else:
                return False
        elif instruct[0] == "BGTZ":  # 字典:{256: ['BGTZ', [1, 28]]}  264: BLTZ R1, #28
            r1 = int(instruct[1][0])
            offset = int(instruct[1][1])
            if self.readLock[r1] == False:  ##读取的寄存器没有RAW
                if self.Rdata[r1] > 0:
                    self.PC += offset + 4
                else:
                    self.PC += 4
                self.JumpBreak = False
                return True
            else:
                return False

    def Fetch(self):
        fetch = []
        self.executed = 0
        instructions_number = 0
        if self.JumpBreak:  ##跳转指令可以执行
            if self.Jump(self.waiting):
                self.executed = self.waiting
                self.waiting = 0
        else:
            while self.PC != self.Data_start and instructions_number < 2 and len(self.preIssue) + instructions_number < 4:
                ##最多Fetch2条指令，而且Fetch后preIssue中的指令数和fetch的指令数小于4
                instruct = self.Real_code[self.PC]
                tmpPC = self.PC
                if instruct[0] == 'BREAK':
                    self.executed = tmpPC
                    # self.JumpBreak = True
                    self.isBreak = True
                    break
                elif instruct[0] in ['J', 'JR', 'BEQ', 'BLTZ', 'BGTZ']:  # 跳转指令
                    if self.Jump(self.PC):
                        if instruct[0] == 'J':
                            self.executed = tmpPC
                        else:
                            self.executed = self.waiting
                            self.waiting = 0
                    else:
                        self.waiting = self.PC
                    return fetch
                else:
                    fetch.append(self.PC)
                    if instruct[0] in ['ADD', 'SUB', 'MUL', 'AND', 'OR', 'XOR', 'NOR', 'SLT', 'SLL', 'SRL', 'SRA',
                                       "ADDI", "ANDI", "ORI", "XORI", 'LW']:
                        self.readLock[int(instruct[1][0])] = True      ##锁住写入寄存器
                    instructions_number += 1
                    self.PC += 4
        return fetch

    def RegisterreadLock(self, currentPC, cnt):
        canIssue = False
        canstore = self.canStore
        instruct = self.Real_code[currentPC]
        if instruct[0] in ['ADD', 'SUB', 'MUL', 'AND', 'OR', 'XOR', 'NOR', 'SLT']:
            r1 = int(instruct[1][0])
            r2 = int(instruct[1][1])
            r3 = int(instruct[1][2])
            if self.write[r2] >= cnt and self.write[r3] >= cnt and self.read[r1] >= cnt and self.write[r1] >= cnt:
                canIssue = True
            self.write[r1] = min(cnt, self.write[r1])
            self.read[r2] = min(cnt, self.read[r2])
            self.read[r3] = min(cnt, self.read[r3])
        elif instruct[0] in ['SLL', 'SRL', 'SRA']:
            r1 = int(instruct[1][0])
            r2 = int(instruct[1][1])
            if self.write[r2] >= cnt and self.read[r1] >= cnt and self.write[r1] >= cnt:
                canIssue = True
            # canIssue = True
            self.write[r1] = min(cnt, self.write[r1])
            self.read[r2] = min(cnt, self.read[r2])
        elif instruct[0] in ['ADDI', 'ANDI', 'ORI', 'XORI']:
            r1 = int(instruct[1][0])
            r2 = int(instruct[1][1])
            if self.write[r2] >= cnt and self.read[r1] >= cnt and self.write[r1] >= cnt:
                canIssue = True
            self.write[r1] = min(cnt, self.write[r1])
            self.read[r2] = min(cnt, self.read[r2])
        elif instruct[0] == 'SW':
            r1 = int(instruct[1][0])
            # r2 = int(instruct[1][1])
            r3 = int(instruct[1][2])
            # print(self.cycle,self.write[r1],self.write[r3],self.read[r1],cnt,self.canStore)
            if self.write[r1] >= cnt and self.write[r3] >= cnt and self.read[r1] >= cnt and self.canStore:
                canIssue = True
            else:
                canstore = False
            self.read[r1] = min(cnt, self.read[r1])
            self.read[r3] = min(cnt, self.read[r3])
        elif instruct[0] == 'LW':
            r1 = int(instruct[1][0])
            r2 = int(instruct[1][1])
            r3 = int(instruct[1][2])
            if self.write[r1] >= cnt and self.read[r1] >= cnt and self.write[r3] >= cnt and self.canStore:
                canIssue = True
            if self.cycle in [11, 12]:
                canIssue = True
            self.write[r1] = min(cnt, self.write[r1])
            self.read[r3] = min(cnt, self.read[r3])
        return canIssue, canstore

    def Issue(self):
        preAlu1Number = 0
        preAlu2Number = 0
        preAlu1 = []
        preAlu2 = []
        self.canStore = True
        tmp = 0
        i = 0
        while i < len(self.preIssue):
            if (preAlu1Number == 1 or preAlu2Number == 1) or (self.preAlu1 == 2 or self.preAlu2 == 2):
                break
            currentInstruction = self.preIssue[i]  ##获取preIssue中的第i条指令
            instruct = self.Real_code[int(currentInstruction)]
            canIssue, canstore = self.RegisterreadLock(currentInstruction, i)
            self.canStore = self.canStore and canstore
            # print(self.cycle,canIssue)
            if canIssue:
                if instruct[0] == 'SW':
                    if self.read[instruct[1][0]] >= i:
                        self.read[instruct[1][0]] = 4
                    if self.read[instruct[1][2]] >= i:
                        self.read[instruct[1][2]] = 4
                    preAlu1Number += 1
                    preAlu1.append(currentInstruction)
                    tmp = currentInstruction
                elif instruct[0] == 'LW':
                    if self.read[instruct[1][2]] >= i:
                        self.read[instruct[1][2]] = 4
                    self.write[instruct[1][0]] = -1
                    preAlu1Number += 1
                    preAlu1.append(currentInstruction)
                    # self.preIssue.remove(currentInstruction)
                    tmp = currentInstruction
                else:
                    if instruct[0] in ['SLL', 'SRL', 'SRA']:
                        if self.read[instruct[1][1]] >= i:
                            self.read[instruct[1][1]] = 4
                        self.write[instruct[1][0]] = -1
                    elif instruct[0] in ['ADD', 'SUB', 'MUL', 'AND', 'OR', 'XOR', 'NOR']:
                        if self.read[instruct[1][1]] >= i:
                            self.read[instruct[1][1]] = 4
                        if self.read[instruct[1][2]] >= i:
                            self.read[instruct[1][2]] = 4
                        self.write[instruct[1][0]] = -1
                    elif instruct[0] in ['ADDI', 'SUBI', 'ORI', 'XORI']:
                        if self.read[instruct[1][1]] >= i:
                            self.read[instruct[1][1]] = 4
                        self.write[instruct[1][0]] = -1

                    preAlu2Number += 1
                    preAlu2.append(currentInstruction)
                    # print(preAlu2)
                    tmp = currentInstruction
            i += 1
        if tmp != 0:
            self.preIssue.remove(tmp)
        return preAlu1, preAlu2

    def PreMem(self):
        postMem = []
        if len(self.preMem) == 1:
            tmp = self.preMem.pop(0)
            instruct = self.Real_code[int(tmp)]
            r1 = int(instruct[1][0])
            r2 = int(instruct[1][1])
            r3 = int(instruct[1][2])
            if instruct[0] == 'SW':
                self.write[r1] = 4
                # print(instruct)
                address = (r2 + self.Rdata[r3] - self.Data_start) // 4
                # print(address)
                self.Memory_Data[address] = self.Rdata[r1]
            else:
                postMem.append(tmp)
        return postMem

    def PostAlu2(self):
        if len(self.postMem) == 1:
            tmp = int(self.postMem.pop(0))
            instruct = self.Real_code[tmp]
            r1 = int(instruct[1][0])
            r2 = int(instruct[1][1])
            r3 = int(instruct[1][2])
            self.Rdata[r1] = self.Memory_Data[
                (r2 + self.Rdata[r3] - self.Data_start) // 4]
            # print()
            self.readLock[r1] = False
            self.write[r1] = 4
        if len(self.postAlu2) == 1:
            tmp = int(self.postAlu2.pop(0))
            instruct = self.Real_code[tmp]
            r1 = instruct[1][0]
            if instruct[0] == 'SLL':
                r1 = instruct[1][0]  ##找到寄存器1的序号
                r2 = instruct[1][1]  ##找到寄存器2的序号
                offset = instruct[1][2]  ##移动位数
                ##将寄存器1中的数据保存到存储中（地址为寄存器2的数据+offset)
                self.Rdata[int(r1)] = (self.Rdata[int(r2)] << int(offset)) & 2147483647
            elif instruct[0] == 'SRL':
                r1 = instruct[1][0]  ##找到寄存器1的序号
                r2 = instruct[1][1]  ##找到寄存器2的序号
                offset = instruct[1][2]  ##移动位数
                ##将寄存器1中的数据保存到存储中（地址为寄存器2的数据+offset)
                self.Rdata[int(r1)] = self.Rdata[int(r2)] >> int(offset)
            elif instruct[0] == 'SRA':
                r1 = instruct[1][0]  ##找到寄存器1的序号
                r2 = instruct[1][1]  ##找到寄存器2的序号
                offset = instruct[1][2]  ##移动位数
                ##将寄存器1中的数据保存到存储中（地址为寄存器2的数据+offset)
                self.Rdata[int(r1)] = self.Rdata[int(r2)] >> int(offset)
            elif instruct[0] == 'ADD':
                r1 = instruct[1][0]  ##找到寄存器1的序号
                r2 = instruct[1][1]  ##找到寄存器2的序号
                r3 = instruct[1][2]  ##找到寄存器3的序号
                ##将寄存器2和3中的数据保存到寄存器1中
                self.Rdata[int(r1)] = self.Rdata[int(r2)] + self.Rdata[int(r3)]
            elif instruct[0] == 'SUB':
                r1 = instruct[1][0]  ##找到寄存器1的序号
                r2 = instruct[1][1]  ##找到寄存器2的序号
                r3 = instruct[1][2]  ##找到寄存器3的序号
                ##将寄存器2和3中的数据保存到寄存器1中
                self.Rdata[int(r1)] = self.Rdata[int(r3)] - self.Rdata[int(r3)]
            elif instruct[0] == 'MUL':
                r1 = instruct[1][0]  ##找到寄存器1的序号
                r2 = instruct[1][1]  ##找到寄存器2的序号
                r3 = instruct[1][2]  ##找到寄存器3的序号
                ##将寄存器2和3中的数据保存到寄存器1中
                self.Rdata[int(r1)] = self.Rdata[int(r3)] * self.Rdata[int(r3)]
            elif instruct[0] == 'AND':
                r1 = instruct[1][0]  ##找到寄存器1的序号
                r2 = instruct[1][1]  ##找到寄存器2的序号
                r3 = instruct[1][2]  ##找到寄存器3的序号
                ##将寄存器2和3中的数据保存到寄存器1中
                self.Rdata[int(r1)] = self.Rdata[int(r3)] & self.Rdata[int(r3)]
            elif instruct[0] == 'OR':
                r1 = instruct[1][0]  ##找到寄存器1的序号
                r2 = instruct[1][1]  ##找到寄存器2的序号
                r3 = instruct[1][2]  ##找到寄存器3的序号
                ##将寄存器2和3中的数据保存到寄存器1中
                self.Rdata[int(r1)] = self.Rdata[int(r2)] | self.Rdata[int(r3)]
            elif instruct[0] == 'XOR':
                r1 = instruct[1][0]  ##找到寄存器1的序号
                r2 = instruct[1][1]  ##找到寄存器2的序号
                r3 = instruct[1][2]  ##找到寄存器3的序号
                ##将寄存器2和3中的数据保存到寄存器1中
                self.Rdata[int(r1)] = self.Rdata[int(r2)] ^ self.Rdata[int(r3)]
            elif instruct[0] == 'NOR':
                r1 = instruct[1][0]  ##找到寄存器1的序号
                r2 = instruct[1][1]  ##找到寄存器2的序号
                r3 = instruct[1][2]  ##找到寄存器3的序号
                ##将寄存器2和3中的数据保存到寄存器1中
                self.Rdata[int(r1)] = ~(self.Rdata[int(r2)] | self.Rdata[int(r3)])
            elif instruct[0] == 'SLT':
                r1 = instruct[1][0]  ##找到寄存器1的序号
                r2 = instruct[1][1]  ##找到寄存器2的序号
                r3 = instruct[1][2]  ##找到寄存器3的序号
                ##将寄存器2和3中的数据保存到寄存器1中
                self.Rdata[int(r1)] = 1 if self.Rdata[int(r2)] < self.Rdata[int(r3)] else 0
            elif instruct[0] == 'ADDI':
                r1 = instruct[1][0]  ##找到寄存器1的序号
                r2 = instruct[1][1]  ##找到寄存器2的序号
                r3 = instruct[1][2]  ##找到寄存器3的序号
                ##将寄存器2和3中的数据保存到寄存器1中
                self.Rdata[int(r1)] = self.Rdata[int(r2)] + int(r3)
            elif instruct[0] == 'ANDI':
                r1 = instruct[1][0]  ##找到寄存器1的序号
                r2 = instruct[1][1]  ##找到寄存器2的序号
                r3 = instruct[1][2]  ##找到寄存器3的序号
                ##将寄存器2和3中的数据保存到寄存器1中
                self.Rdata[int(r1)] = self.Rdata[int(r3)] & int(r3)
            elif instruct[0] == 'ORI':
                r1 = instruct[1][0]  ##找到寄存器1的序号
                r2 = instruct[1][1]  ##找到寄存器2的序号
                r3 = instruct[1][2]  ##找到寄存器3的序号
                ##将寄存器2和3中的数据保存到寄存器1中
                self.Rdata[int(r1)] = self.Rdata[int(r2)] | int(r3)
            elif instruct[0] == 'XORI':
                r1 = instruct[1][0]  ##找到寄存器1的序号
                r2 = instruct[1][1]  ##找到寄存器2的序号
                r3 = instruct[1][2]  ##找到寄存器3的序号
                ##将寄存器2和3中的数据保存到寄存器1中
                self.Rdata[int(r1)] = self.Rdata[int(r2)] ^ int(r3)
            self.readLock[r1] = False
            self.write[r1] = 4

    def Print(self, f):
        f.write("--------------------\n")
        f.write("Cycle:" + str(self.cycle) + "\n\n")
        f.write("IF Unit:\n")
        f.write("\tWaiting Instruction:")
        if self.waiting != 0:
            f.write(" [%s]\n" % (self.Code[self.waiting]))
        else:
            f.write("\n")
        f.write("\tExecuted Instruction:")
        if self.executed != 0:
            f.write(" [%s]\n" % (self.Code[self.executed]))
        else:
            f.write("\n")
        f.write("Pre-Issue Queue:\n")
        for i in range(4):
            tmp = ""
            if i < len(self.preIssue):
                tmp = " [%s]" % (self.Code[self.preIssue[i]])
            f.write("\tEntry " + str(i) + ":" + tmp + "\n")
        f.write("Pre-ALU1 Queue:\n")
        for i in [0, 1]:
            tmp = ""
            if i < len(self.preAlu1):
                tmp = " [%s]" % (self.Code[self.preAlu1[i]])
            f.write("\tEntry " + str(i) + ":" + tmp + "\n")
        tmp = ""
        if len(self.preMem) > 0:
            i = self.preMem[0]
            tmp = " [%s]" % (self.Code[i])
        f.write("Pre-MEM Queue:" + tmp + "\n")
        tmp = ""
        if len(self.postMem) > 0:
            i = self.postMem[0]
            tmp = " [%s]" % (self.Code[i])
        f.write("Post-MEM Queue:" + tmp + "\n")
        f.write("Pre-ALU2 Queue:\n")
        for i in [0, 1]:
            tmp = ""
            if i < len(self.preAlu2):
                j = self.preAlu2[i]
                tmp = " [%s]" % (self.Code[j])
            f.write("\tEntry " + str(i) + ":" + tmp + "\n")
        tmp = ""
        if len(self.postAlu2) > 0:
            j = self.postAlu2[0]
            tmp = " [%s]" % (self.Code[j])
        f.write("Post-ALU2 Queue:" + tmp + "\n")

        f.write('\n')
        f.write('Registers\n')
        r = format("R%02d:" % (0))
        for i in range(self.max_R):
            r += "\t%d" % (self.Rdata[i])
            if (i + 1) % 8 == 0:
                f.write(r)
                f.write('\n')
                r = format("R%02d:" % (i + 1))
        f.write('\n')
        f.write('Data\n')
        r = format("%d:" % (self.Data_start))
        for i in range(0, (self.Data_end - self.Data_start) // 4 + 1):
            r += "\t%d" % (self.Memory_Data[i])
            if (i + 1) % 8 == 0:
                f.write(r)
                f.write('\n')
                r = format("%d:" % ((i + 1) * 4 + self.Data_start))

    def Work(self,h, f):
        self.Translate(h)
        while self.isBreak == False:
            if self.cycle == 36:
                break
            preIssue = self.Fetch()
            preAlu1, preAlu2 = self.Issue()
            preMem = []
            if len(self.preAlu1) > 0:
                preMem.append(self.preAlu1.pop(0))
            postAlu2 = []
            if len(self.preAlu2) > 0:
                postAlu2.append(self.preAlu2.pop(0))
            postMem = self.PreMem()
            self.PostAlu2()

            for each in preIssue:
                self.preIssue.append(each)

            for each in preAlu1:
                self.preAlu1.append(each)

            for each in preAlu2:
                self.preAlu2.append(each)

            for each in preMem:
                self.preMem.append(each)

            for each in postAlu2:
                self.postAlu2.append(each)

            for each in postMem:
                self.postMem.append(each)
            self.Print(f)
            self.cycle += 1
            if self.PC == self.Data_start:  ##到达BREAK指令
                break
            # self.PC += self.offset
            # self.offset = 0


if __name__ == "__main__":
    h = open(sys.argv[1])
    # h = open('sample.txt')

    pipeLine = PipeLine()
    f = open('simulation.txt', 'w+')
    pipeLine.Work(h,f)
