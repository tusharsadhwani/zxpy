~'echo hi'

for i in range(10):
    ~f'printf {i} %b'
else:
    ~'echo'


def main():
    ~'echo hello, this is main.'

    for var in ['abc', 'xyz']:
        ~f'echo var={var!r}'


main()
