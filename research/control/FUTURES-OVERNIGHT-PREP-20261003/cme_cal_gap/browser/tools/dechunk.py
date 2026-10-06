import sys
def dechunk(b):
    out = b""
    i = 0
    while True:
        j = b.find(b"\r\n", i)
        if j < 0: break
        try: n = int(b[i:j], 16)
        except ValueError:
            out += b[i:]; break
        if n == 0: break
        out += b[j+2:j+2+n]
        i = j + 2 + n + 2
    return out
if __name__ == "__main__":
    sys.stdout.buffer.write(dechunk(sys.stdin.buffer.read()))
