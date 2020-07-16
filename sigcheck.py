import numpy as np
import os
from numba import jit, njit
import re


def getbits(name, n):
    data = np.fromfile(name, dtype = np.uint8)
    fragments = chunks(data, n)
    bits = []
    for frag in fragments:
        bit_chunk = np.unpackbits(frag)
        bits.append(bit_chunk)
    return bits

@njit
def chunks(lst, n):
    out = []
    if n==0:
        out.append(lst)
        return out
    for i in range(0, len(lst), n):
        out.append(lst[i:i + n])
    return out


def make_2D_array(lis):
    n = len(lis)
    lengths = np.array([len(x) for x in lis], dtype = int)
    max_len = np.max(lengths)
    arr = np.zeros((n, max_len), dtype = np.uint8)

    for i in range(n):
        arr[i, :lengths[i]] = lis[i]
    return arr, lengths

@njit
def jumps_map(string, star = 1):
    count = 0
    jumps = []
    for i in range(len(string)):
        if string[i] == '?':
            count += 1
        elif string[i] == '*':
            count += star
        elif count > 0:
            jumps.append(count)
            count = 0
        elif i == 0:
            jumps.append(count)
    jumps.append(count)
    return np.array(jumps, dtype = np.uint16)

def list_size(lst):
    return sum([len(el) for el in lst])

def cut(string):
    s1 = string.split('?')
    temp = []
    for el in s1:
        if el != None:
            temp += filter(None, el.split('*'))
    out = []
    for t in temp:
        out.append([int(d) for d in str(t)])
    return out


@njit
def check(bits, pattern, i, jumps, lenghts):
    last_j = jumps[-1]
    offset = jumps[0]
    for j in range(len(pattern)):
        l = lenghts[j]
        if (i+l+offset+last_j > len(bits)):
            return False
        if (bits[i+offset] == pattern[j][0]) and np.array_equal(bits[i+offset:i+l+offset], pattern[j][:l]):
            offset += l
            offset += jumps[j+1]
        else:
            return False
    return True
            

@njit
def subcount_even(bits, pattern, coupling=True):
    count = 0
    pat_len = len(pattern)
    if coupling:
        step = 1
    else:
        step = pat_len
    for i in range(0,len(bits),step):
        if (bits[i] == pattern[0]) and np.array_equal(bits[i:i+pat_len],pattern):
            count += 1
    return count

@njit
def subcount_uneven(bits, pattern, lengths, jumps, pat_len, coupling=True):
    count = 0
    if coupling:
        step = 1
    else:
        step = pat_len

    for i in range(0,len(bits),step):
        if check(bits, pattern, i, jumps, lengths) == True:
            count += 1
    return count

def subcount(bits, pattern_str, star = 1, coupling = True):
    jumps = jumps_map(pattern_str, star)
    
    if all(jumps == 0):
        pattern = np.array(list(map(int, pattern_str)), dtype = np.uint8)
        count = subcount_even(bits, pattern, coupling)
    else:
        pat = cut(pattern_str)
        pattern, lengths = make_2D_array(pat)
        pat_len = list_size(pattern) + sum(jumps)
        count = subcount_uneven(bits, pattern, lengths, jumps, pat_len, coupling)
    return count