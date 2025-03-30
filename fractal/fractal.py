"""
Mandelbrot Fractal Analysis for Time Series - Robust Version
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import linregress
from numpy import log, polyfit, sqrt, std, subtract
import yfinance as yf
import warnings

# Suppress runtime warnings for cleaner output
warnings.filterwarnings("ignore", category=RuntimeWarning)

# Set random seed for reproducibility
np.random.seed(42)

# ======================
# 1. Data Generation
# ======================

def generate_fractal_time_series(length=1000, hurst=0.7):
    """Generate a fractal time series with a given Hurst exponent"""
    steps = np.random.normal(0, 1, length)
    fgn = np.zeros(length)
    fgn[0] = steps[0]
    for i in range(1, length):
        fgn[i] = fgn[i-1] + steps[i] * (i**(2*hurst - 2))
    return (fgn - np.min(fgn)) / (np.max(fgn) - np.min(fgn))

# ======================
# 2. Analysis Functions (Improved)
# ======================

def hurst_exponent(time_series, max_lag=50):
    """Robust Hurst exponent calculation"""
    if len(time_series) < max_lag:
        max_lag = len(time_series) // 2

    lags = range(2, max_lag)
    tau = []
    for lag in lags:
        if lag >= len(time_series):
            continue
        diff = np.subtract(time_series[lag:], time_series[:-lag])
        if len(diff) > 0:
            tau.append(np.std(diff))

    if len(tau) < 2:
        return np.nan

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        poly = np.polyfit(np.log(lags[:len(tau)]), np.log(tau), 1)
    return poly[0]

def safe_mfdfa(time_series, q_list=np.linspace(-5, 5, 11), scale_min=10, scale_max=None):
    """Robust MF-DFA implementation"""
    n = len(time_series)
    if n < 100:
        return np.full(len(q_list), np.nan), np.full(len(q_list), np.nan), np.full(len(q_list), np.nan), np.full(len(q_list), np.nan)

    if scale_max is None:
        scale_max = n // 4

    scales = np.unique(np.logspace(np.log10(scale_min), np.log10(scale_max), num=20, dtype=int))
    scales = scales[(scales >= scale_min) & (scales <= scale_max)]

    y = np.cumsum(time_series - np.mean(time_series))
    F_q = np.zeros((len(scales), len(q_list)))

    for i, s in enumerate(scales):
        Ns = n // s
        if Ns < 1:
            continue

        segments = y[:Ns*s].reshape(Ns, s)
        for v in range(Ns):
            x = np.arange(s)
            p = np.polyfit(x, segments[v], 1)
            segments[v] = segments[v] - np.polyval(p, x)

        F2 = np.var(segments, axis=1)
        F2 = F2[~np.isnan(F2)]

        for j, q in enumerate(q_list):
            if len(F2) == 0:
                F_q[i, j] = np.nan
                continue

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                if q == 0:
                    F_q[i, j] = np.exp(0.5 * np.mean(np.log(F2[F2 > 0])))
                else:
                    F_q[i, j] = np.mean(F2 ** (q/2)) ** (1/q) if len(F2) > 0 else np.nan

    h_q = np.zeros(len(q_list))
    for j, q in enumerate(q_list):
        valid = ~np.isnan(F_q[:, j])
        if np.sum(valid) < 2:
            h_q[j] = np.nan
            continue

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            slope = linregress(np.log(scales[valid]), np.log(F_q[valid, j])).slope
        h_q[j] = slope

    tau = q_list * h_q - 1
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        alpha = np.gradient(tau, q_list[1]-q_list[0])
    f_alpha = q_list * alpha - tau

    return h_q, tau, alpha, f_alpha

def robust_fractal_dimension(time_series, k_max=10):
    """Improved fractal dimension calculation"""
    n = len(time_series)
    if n < k_max:
        return np.nan

    L = np.zeros(k_max)
    for k in range(1, k_max+1):
        step = max(1, k)
        diff = np.diff(time_series[::step])
        if len(diff) > 0:
            L[k-1] = np.sum(np.abs(diff)) * (n / (n//step))

    valid = (L > 0) & ~np.isnan(L) & ~np.isinf(L)
    if np.sum(valid) < 2:
        return np.nan

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        slope = linregress(np.log(np.arange(1, k_max+1)[valid]), np.log(L[valid])).slope
    return 1 - slope

# ======================
# 3. Visualization
# ======================

def plot_results(ts, hurst, h_q, tau, alpha, f_alpha, fd, title=""):
    """Visualize analysis results"""
    plt.figure(figsize=(18, 10))

    plt.subplot(2, 3, 1)
    plt.plot(ts)
    plt.title(f"{title}\nHurst: {hurst:.3f}, FD: {fd:.3f}")

    plt.subplot(2, 3, 2)
    plt.plot(q_list, h_q, 'o-')
    plt.xlabel('q')
    plt.ylabel('h(q)')
    plt.title('Generalized Hurst exponent')

    plt.subplot(2, 3, 3)
    plt.plot(q_list, tau, 'o-')
    plt.xlabel('q')
    plt.ylabel('τ(q)')
    plt.title('Mass exponent')

    plt.subplot(2, 3, 4)
    plt.plot(alpha, f_alpha, 'o-')
    plt.xlabel('α')
    plt.ylabel('f(α)')
    plt.title('Multifractal spectrum')

    plt.tight_layout()
    plt.show()

# ======================
# 4. Main Analysis
# ======================

if __name__ == "__main__":
    # Parameters
    length = 5000
    hurst_param = 0.72
    q_list = np.linspace(-5, 5, 11)  # Reduced for stability

    print("=== Synthetic Data Analysis ===")
    ts = generate_fractal_time_series(length=length, hurst=hurst_param)

    hurst = hurst_exponent(ts)
    h_q, tau, alpha, f_alpha = safe_mfdfa(ts, q_list=q_list)
    fd = robust_fractal_dimension(ts)

    print(f"Hurst exponent: {hurst:.4f}")
    print(f"Fractal dimension: {fd:.4f}")
    print(f"Expected Hurst: {hurst_param:.4f}")

    plot_results(ts, hurst, h_q, tau, alpha, f_alpha, fd, "Synthetic Data")

    print("\n=== Financial Data Analysis S&P 500 ===")
    try:
        # Download S&P 500 data with adjusted parameters
        sp500 = yf.download('^GSPC', start='2015-01-01', end='2023-01-01', progress=False)
        if len(sp500) < 100:
            raise ValueError("Not enough data points")

        returns = np.diff(np.log(sp500['Close'].values))
        returns = returns[~np.isnan(returns)]

        if len(returns) < 100:
            raise ValueError("Not enough valid returns")

        hurst_fin = hurst_exponent(returns, max_lag=min(100, len(returns)//2))
        fd_fin = robust_fractal_dimension(returns)
        h_q_fin, tau_fin, alpha_fin, f_alpha_fin = safe_mfdfa(returns, q_list=q_list)

        print(f"S&P 500 Log Returns Analysis:")
        print(f"Hurst exponent: {hurst_fin:.4f}")
        print(f"Fractal dimension: {fd_fin:.4f}")

        plot_results(returns, hurst_fin, h_q_fin, tau_fin, alpha_fin, f_alpha_fin, fd_fin, "S&P 500 Log Returns")

    except Exception as e:
        print(f"Financial data analysis failed: {str(e)}")
        print("Trying with cached sample data...")

        # Fallback to sample data if download fails
        try:
            sample_data = pd.read_csv('https://raw.githubusercontent.com/selva86/datasets/master/a10.csv', parse_dates=['date'])
            ts_sample = sample_data['value'].values
            ts_sample = (ts_sample - np.nanmean(ts_sample)) / np.nanstd(ts_sample)

            hurst_sample = hurst_exponent(ts_sample)
            fd_sample = robust_fractal_dimension(ts_sample)
            h_q_sample, tau_sample, alpha_sample, f_alpha_sample = safe_mfdfa(ts_sample, q_list=q_list)

            print("\nSample Data Analysis:")
            print(f"Hurst exponent: {hurst_sample:.4f}")
            print(f"Fractal dimension: {fd_sample:.4f}")

            plot_results(ts_sample, hurst_sample, h_q_sample, tau_sample,
                        alpha_sample, f_alpha_sample, fd_sample, "Sample Time Series")

        except Exception as e2:
            print(f"Could not load sample data either: {str(e2)}")