TRADING_DAYS_PER_YEAR = 252

# ACF/PACF diagnostics
ACF_LAGS = 40
ACF_YLIM = (-0.3, 0.3)

# Trend and volatility diagnostics
HURST_WINDOW = 252
VOL_SHORT_WINDOW = 20
VOL_LONG_WINDOW = 60
ATR_WINDOW = 14

# Cross-sectional signal checks
N_QUANTILES = 5
QUANTILE_TESTS = [
    ("STR_21D", 21, 21),
    ("MOM_126D", 126, 21),
]
