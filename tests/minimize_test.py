import numpy as np
import scipy
import random
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
random.seed(42);

def quadFunc(x, a, b, c):
    y = [];
    for curr_x in x:
        y.append(a*curr_x*curr_x+b*curr_x+c);
    return y

my_x = np.arange(-20,21);
my_x = my_x.astype(np.double);
my_y = quadFunc(my_x, *[9, 18, 20]);

for y_idx in range(len(my_y)):
    my_y[y_idx] += random.uniform(-0.5, 0.5);

fit_vals = curve_fit(quadFunc, my_x, my_y, [1,1,1]);
fit_y = quadFunc(my_x, *fit_vals[0]);

print(fit_vals[0]);


fig,ax = plt.subplots(1,1)

ax.plot(my_x, my_y, 'rh')
ax.plot(my_x, fit_y, 'b--')

plt.show();
