~'echo hi'

for i in range(1, 5):
    ~f'seq 1 {i} | xargs echo'
else:
    ~'echo done'


def main():
    ~'echo hello, this is main.'

    for var in ['abc', 'xyz']:
        ~f'echo var={var!r}'


main()
