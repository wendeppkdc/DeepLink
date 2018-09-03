# Add zeros (and plus 1) before num to to match Semlink sentence with Deepbank Filename

def addZeros(num):
    s = str(int(num) + 1)
    return "0" * (3 - len(s)) + s