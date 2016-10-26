
def find_key_name(err):
    if err[:4] == 'null':
        first_quote = err.find("\"")
        second_quote = err[first_quote + 1:].find("\"")
        return 'null', err[first_quote + 1: first_quote + 1 + second_quote]
    elif err.find('foreign key'):
        words = 'Key ('
        before_pos = err.find(words)
        after_pos = err[before_pos:].find(')')
        return 'fkey', err[before_pos:][len(words):after_pos]
