import numpy as np
import math


def parse_nash_eq_from_file(filename: str) -> (dict, dict):
    alice_strats: dict = {}
    bob_strats: dict = {}
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line == '-------------':
                continue
            parts = line.split()
            player = parts[0]
            strat_start = line.index('[')
            strat_end = line.index(']')
            strat_str = line[strat_start+1:strat_end]
            strat_values: list = []
            for val_str in strat_str.split(','):
                val_str = val_str.strip()
                if 'np.int64(' in val_str:
                    val = int(val_str.split('(')[1].split(')')[0])
                else:
                    val = int(val_str)
                strat_values.append(val)
            prob = float(parts[-1])
            strat_tuple = tuple(strat_values)
            if player == "Alice":
                alice_strats[strat_tuple] = prob
            else:
                bob_strats[strat_tuple] = prob
    return alice_strats, bob_strats


def cartesian(arrays, out = None):
    arrays = [np.asarray(x) for x in arrays]
    dtype = arrays[0].dtype

    cn = np.prod([x.size for x in arrays])
    if out is None:
        out = np.zeros([cn, len(arrays)], dtype = dtype)

    cm = int(cn / arrays[0].size)
    out[:,0] = np.repeat(arrays[0], cm)

    if arrays[1:]:
        cartesian(arrays[1:], out = out[0:cm, 1:])
        for j in range(1, arrays[0].size):
            out[j*cm:(j+1)*cm, 1:] = out[0:cm, 1:]

    return out
