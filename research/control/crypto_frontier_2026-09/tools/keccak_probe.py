"""Pure-python keccak256 (self-tested) + event topic computation. Light survey tooling."""
import json, os
RC = [
0x0000000000000001,0x0000000000008082,0x800000000000808A,0x8000000080008000,
0x000000000000808B,0x0000000080000001,0x8000000080008081,0x8000000000008009,
0x000000000000008A,0x0000000000000088,0x0000000080008009,0x000000008000000A,
0x000000008000808B,0x800000000000008B,0x8000000000008089,0x8000000000008003,
0x8000000000008002,0x8000000000000080,0x000000000000800A,0x800000008000000A,
0x8000000080008081,0x8000000000008080,0x0000000080000001,0x8000000080008008]
ROT = [[0,36,3,41,18],[1,44,10,45,2],[62,6,43,15,61],[28,55,25,21,56],[27,20,39,8,14]]
M = (1<<64)-1
def _rol(x,n): n%=64; return ((x<<n)|(x>>(64-n)))&M
def keccak256(msg: bytes) -> bytes:
    rate=136; A=[[0]*5 for _ in range(5)]
    data=msg+b'\x01'+b'\x00'*((rate-len(msg)-2)%rate)+b'\x80'
    # pad10*1 multi-rate: append 0x01 ... 0x80 in last byte of block
    blocks=[data[i:i+rate] for i in range(0,len(data),rate)] if data else []
    for blk in blocks:
        for i in range(rate//8):
            w=int.from_bytes(blk[8*i:8*i+8],'little')
            A[i%5][i//5]^=w
        # keccak-f
        for rnd in range(24):
            C=[A[x][0]^A[x][1]^A[x][2]^A[x][3]^A[x][4] for x in range(5)]
            D=[C[(x-1)%5]^_rol(C[(x+1)%5],1) for x in range(5)]
            for x in range(5):
                for y in range(5): A[x][y]^=D[x]
            B=[[0]*5 for _ in range(5)]
            for x in range(5):
                for y in range(5): B[y][(2*x+3*y)%5]=_rol(A[x][y],ROT[x][y])
            for x in range(5):
                for y in range(5): A[x][y]=B[x][y]^((~B[(x+1)%5][y])&M&B[(x+2)%5][y])
            A[0][0]^=RC[rnd]
    out=b''
    for i in range(4):
        for y in range(5):
            for x in range(5):
                if i*5+x<17: pass
    # squeeze 32 bytes: take lanes in order (x,y): index i -> x=i%5,y=i//5
    lanes=[]
    for i in range(4):
        x,y=i%5,i//5
        lanes.append(A[x][y].to_bytes(8,'little'))
    return b''.join(lanes)[:32]
if __name__=='__main__':
    assert keccak256(b'').hex()=='c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470', "EMPTY VECTOR FAIL"
    assert keccak256(b'abc').hex()=='4e03657aea45a94fc7d47ba826c8d667c0d1e6e33a64a036ec44f58fa12d6c45', "ABC VECTOR FAIL"
    sigs={
      "Mint(address,address,uint256)":None,
      "Burn(address,uint256)":None,
      "Issue(uint256)":None,
      "Redeem(uint256)":None,
      "Transfer(address,address,uint256)":None,
    }
    out={s:('0x'+keccak256(s.encode()).hex()) for s in sigs}
    assert out["Transfer(address,address,uint256)"]=="0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef", "TRANSFER VECTOR FAIL"
    print(json.dumps({"self_test":"PASS","topics":out},indent=1))
