import os
from urllib.request import urlopen

from cryptography.hazmat.primitives import hashes
import itertools
import string
from time import perf_counter


def guess_password_brute(password_hash):
    chars = string.ascii_lowercase + string.digits
    attempts = 0
    start_time = perf_counter()
    for password_length in range(1, 9):
        for guess in itertools.product(chars, repeat=password_length):
            attempts += 1
            guess = ''.join(guess)
            brute_digest = hashes.Hash(hashes.SHA3_512())
            brute_digest.update(str.encode(guess))
            guess_hash = brute_digest.finalize()
            if guess_hash == password_hash:
                print("Password Found in ", perf_counter() - start_time, "seconds.")
                return 'password is {}. found in {} guesses.'.format(guess, attempts)


def guess_password_dict(password_hash):
    url = 'https://raw.githubusercontent.com/berzerk0/Probable-Wordlists/master/Real-Passwords/Top12Thousand-probable-v2.txt'
    wordlist = urlopen(url).read().decode('UTF-8')
    guesspasswordlist = wordlist.split('\n')
    attempts = 0
    start_time = perf_counter()
    for guess in guesspasswordlist:
        attempts += 1
        dict_digest = hashes.Hash(hashes.SHA3_512())
        dict_digest.update(str.encode(guess))
        guess_hash = dict_digest.finalize()
        if guess_hash == password_hash:
            print("Password Found in ", perf_counter() - start_time, "seconds.")
            return 'password is {}. found in {} guesses.'.format(guess, attempts)


if __name__ == "__main__":
    digest = hashes.Hash(hashes.SHA3_512())
    digest.update(str.encode("aa"))  # ENTER THE PASSWORD TO BE CRACKED HERE
    hash_value = digest.finalize()
    print("Brute Force Results")
    print(guess_password_brute(hash_value))
    print()
    print("Dictionary Attack Results")
    print(guess_password_dict(hash_value))
