import numpy as np
import matplotlib.pyplot as plt
from scipy.io import savemat

fs = int(200e3)
decimation = 1024
duration = 15
true_rate = fs / decimation

#file = 'data_test_no_nn.csv'
#file = 'data_test.csv'
file = 'data_bh_3.txt'

data = np.loadtxt(f"/Users/jasondesai/Desktop/Summer_2025/{file}")
#data = np.fromfile("/Users/jasondesai/Desktop/data_test.bin", dtype='<i4')

#data = data[20:]
if (len(data) % 2 == 1):
    data = data[:-1]

samples = len(data) / 2

print('length of data collected = ', samples)

I= data[0::2]
Q = data[1::2]

I_m = I - np.mean(I)
Q_m = Q - np.mean(Q)

z = I_m + 1j*Q_m

savemat("bh_2.mat", {"breath_hold": z})

lamb = int(3e8) / int(24.150e9)
phi = np.unwrap(np.angle(z))
disp = (phi * lamb) / (4 * np.pi)

plt.figure()
plt.plot(I_m, Q_m, '.')
plt.show()

plt.figure()
plt.plot(disp)
plt.show()



t = np.arange(0, duration, 1/true_rate) 

plt.figure()
plt.subplot(2,1,1)
plt.plot(I)
plt.subplot(2,1,2)
plt.plot(Q)
plt.xlabel("Samples")
plt.ylabel("Value")
plt.title("ADC FIFO Data")

plt.figure()
plt.plot(I, Q, '.')
plt.title('Breath-Hold IQ Plot')
plt.xlabel('I channel')
plt.ylabel('Q channel')
plt.axis('square')
plt.show()
