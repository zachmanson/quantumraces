import numpy as np
import math

D = 3651011.631  # difficulty as of Feb 26 2013
gamma = 0.5
def p(k: int, D: float) -> float:
    return np.float64((math.sin(2 * ((k) + 1/2) * math.asin(1/np.sqrt(D))))**2)

x = p(750, D)
y = p(1500, D)


a_100 = x * (1 - x) + gamma * x * x
a_200 = x * (1 - x) * (1 - x) * (1 - x) + gamma * x * x


a_133 = y * (1 - y) + gamma * y * y
a_233 = y * (1 - y) * (1 - y) * (1 - y) + gamma * y * y

a_101 = a_100 
a_201 = x * (1 - x) * (1 - x) + gamma * x * p(1500 - 750, D)

A_00 = a_100 + a_200
print(A_00)

A_33 = a_133 + a_233
print(A_33)

A_01 = a_101 + a_201
print(A_01)