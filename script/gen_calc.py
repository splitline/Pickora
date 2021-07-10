import random
ans = []
for _ in range(20):
    n_num = random.randint(2, 15)
    numlist = []
    for i in range(n_num):
        r = random.randint(0, 1)
        if r == 1:
            numlist.append(round(random.uniform(0, 15), 1))
        if r == 0:
            numlist.append(random.randint(1,15))
    
    eq = []
    op = ['+','-','*','/','//','**','%']
    parentheses = False
    for n in numlist:
        if not parentheses and random.randint(0,2) == 1:
            eq.append('(')
            parentheses = True
        eq.append(str(n))
        if parentheses and random.randint(0,2) == 1:
            eq.append(')')
            parentheses = False
        eq.append(random.choice(op))
    
    eq=''.join(eq[:-1])
    if parentheses:
        eq+=')'
    try:
        ans.append(eval(eq))
        print(f'print({eq})')
    except:
        pass

print(ans)
