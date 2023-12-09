"""
Creates a user ID that has a high uniqueness to it.
"""
import time
import random

def generate_uid():
    KEYS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz112345678910"
    
    imp1 = str(round(time.time()))
    imp2 = str(round(int(imp1) / 16))
    imp3 = "".join(random.sample(KEYS*40, 20))
    imp4 = str(time.time() / 2.3).split(".")[1]
    imp5 = imp2 + imp3

    return imp1 + "".join(random.sample(imp5, len(imp5))) + imp4