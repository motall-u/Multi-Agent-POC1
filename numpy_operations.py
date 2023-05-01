# importing necessary library
import numpy as np

# create two NumPy arrays
arr1 = np.array([1,2,3])
arr2 = np.array([4,5,6])

# adding two arrays element-wise
res = arr1 + arr2
print('Addition of two arrays:', res)

# subtracting two arrays element-wise
res = arr1 - arr2
print('Subtraction of two arrays:', res)

# multiplying two arrays element-wise
res = arr1 * arr2
print('Multiplication of two arrays:', res)

# dividing two arrays element-wise
res = arr1 / arr2
print('Division of two arrays:', res)

# taking squares element-wise
res = np.square(arr1)
print('Square of arr1:', res)
