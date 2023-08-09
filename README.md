# RISC-V Simulator

## usage

First, convert your assembly instruction into binary. (your binary file)

Then, execute this python program with converted binary file.
```shell
python3 ./riscv_sim.py ./your_binary_file
```


## Expected Output

![image](https://github.com/yelm-212/RISC-V-simulator/assets/88075691/46e191ed-ca13-4b5a-858f-1d791c980c00)

# Control Logic(Control Unit)
- `ALUSel`, `RegWEn`, `MemRW`, `ImmSel`, 
`BrUN`, `ASel`, `BSel`, `WBSel`, `PCSel`을 내부 변수로 가지며 생성시 초기화된다.
- 내부 변수가 0,1 이상의 값을 가질 수 있을 경우 
혼동을 피하기 위해 `enum` 자료형으로 설정 
## 내부 함수
  - `setFlags`: instruction 값에 따라 내부 변수 값을 수정한다
  - `setALUSel`: opcode에 따라 `ALUSel` 값을 설정한다.

# Branch Comparator
- `R[rs1]`,`R[rs2]` 값을 비교해 Control Logic에 값을 전달하는 새로운 클래스
- Branch 연산의 종류는
혼동을 피하기 위해 `enum` 자료형으로 설정
## 내부 함수 
- `setBr` : A와 B의 값에 따라 BrEq와 BrLT의 값을 설정한다.
