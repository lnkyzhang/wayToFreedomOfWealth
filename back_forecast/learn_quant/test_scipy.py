import numpy as np
import scipy.stats as stats
import scipy.optimize as opt

norm_dist = stats.norm(loc=0.5, scale=2)
n = 200
dat = norm_dist.rvs(size=n)
print("mean of data is: " + str(np.mean(dat)))
print("median of data is: " + str(np.median(dat)))
print("standard deviation of data is: " + str(np.std(dat)))


mu = np.mean(dat)
sigma = np.std(dat)
stat_val, p_val = stats.kstest(dat, 'norm', (mu, sigma))
print('KS-statistic D = %6.3f p-value = %6.4f' % (stat_val, p_val))


stat_val, p_val = stats.ttest_1samp(dat, 0)
print('One-sample t-statistic D = %6.3f, p-value = %6.4f' % (stat_val, p_val))


norm_dist2 = stats.norm(loc=0.5, scale=1.2)
dat2 = norm_dist2.rvs(size=int(n/2))
stat_val, p_val = stats.ttest_ind(dat, dat2, equal_var=False)
print('Two-sample t-statistic D = %6.3f, p-value = %6.4f' % (stat_val, p_val))

g_dist = stats.gamma(a=2)
print(type(g_dist))
print("quantiles of 2, 4 and 5:")
print(g_dist.cdf([2, 4, 5]))
print("Values of 25%, 50% and 90%:")
print(g_dist.pdf([0.25, 0.5, 0.95]))

norm_dist = stats.norm(loc=0, scale=1.8)
dat = norm_dist.rvs(size=100)
info = stats.describe(dat)
print("dat type is:", type(dat))
print("Data size is: " + str(info[0]))
print("Minimum value is: " + str(info[1][0]))
print("Maximum value is: " + str(info[1][1]))
print("Arithmetic mean is: " + str(info[2]))
print("Unbiased variance is: " + str(info[3]))
print("Biased skewness is: " + str(info[4]))
print("Biased kurtosis is: " + str(info[5]))

norm_dist = stats.norm(loc=0, scale=1.8)
dat = norm_dist.rvs(size=100)
mu, sigma = stats.norm.fit(dat)
print("MLE of data mean:" + str(mu))
print("MLE of data standard deviation:" + str(sigma))
