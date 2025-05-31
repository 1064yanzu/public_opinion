
def test_a():
    global a
    a = input('shuru')
    print(f'a_test{a}')

def test_b():
    print(f'b_test{a}')

for i in range(0,5):
    test_a()
    test_b()