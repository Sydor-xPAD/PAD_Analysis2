from scipy.optimize import minimize
import random

random.seed(42)

class fit_curve:
    def __init__(self):
        self.x_vals = [];
        self.y_vals = [];
        return
    
    def calcErr(self, quad_coeff):
        total_sq_err = 0;
        for pointIdx in range(len(self.x_vals)):
            curr_x = self.x_vals[pointIdx];
            curr_y = self.y_vals[pointIdx];
            calc_y = self.evalPoly(curr_x, quad_coeff);
            total_sq_err += (calc_y-curr_y)**2.0;
        return total_sq_err;
            
    def evalPoly(self, x, quad_coeff):
        return quad_coeff[0]*x**2.0 + quad_coeff[1]*x + quad_coeff[2]


poly1 = fit_curve();
poly2 = fit_curve();

for x in range(-10,10):
    poly1.x_vals.append(x)

for x in poly1.x_vals:
    poly1.y_vals.append(3*x**2.0+2*x+1 + random.random() - 0.5)

for x in range(-10,10):
    poly2.x_vals.append(x)

for x in poly1.x_vals:
    poly2.y_vals.append(-2*x**2.0+4*x+7 + random.random() - 0.5)

    
print("Calculated error with exact match:")
print(poly1.calcErr([3,2,1]))
print(poly2.calcErr([-2,4,7]))

res1 = minimize(poly1.calcErr, [1,1,1], method='nelder-mead');
res2 = minimize(poly2.calcErr, [1,1,1], method='nelder-mead');
print("Calculated polynomical terms:")
print(res1.x)
print(res2.x)
