import Crypto.Util.number
import Crypto.Random

import random
import libnum
import sympy

def singleton(cls):
    instance = [None]

    def wrapper(*args, **kwargs):
        if instance[0] is None:
            instance[0] = cls(*args, **kwargs)
        return instance[0]

    return wrapper

@singleton
class ShamirsThreePass():

    def __init__(self, primesize):
        self.prime = self.generatePrime(primesize)

    def generatePrime(self, number_of_bits):
        return Crypto.Util.number.getPrime(number_of_bits, randfunc=Crypto.Random.get_random_bytes)

    def generateEncryptionKey(self):
        coPrime=0
        while (sympy.gcd(coPrime, self.prime-1)!=1):
            coPrime=random.randint(1, self.prime-1)
        return coPrime

    def generateDecryptionKey(self, encryription_key):
        return libnum.invmod(encryription_key, self.prime-1)

    def encodeMessage(self, message):
        return Crypto.Util.number.bytes_to_long(message.encode('utf-8'))

    def decodeMessage(self, message):
        return Crypto.Util.number.long_to_bytes(message).decode()

    def encrypt(self, encoded_message, encryription_key):
        return pow(encoded_message, encryription_key, self.prime)

    def decrypt(self, encrypted_message, decryption_key):
        return pow(encrypted_message, decryption_key, self.prime)

