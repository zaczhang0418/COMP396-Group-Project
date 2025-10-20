# Project Code Summary

This document explains the purpose of key files in the backtesting framework.

## `analyzers.py`

This file is for analyzing the results of a trading strategy.

- It takes the trading history (equity curve) and calculates performance metrics.
- Key metrics include:
    - **Sharpe Ratio:** Measures risk-adjusted return.
    - **Max Drawdown:** The largest drop in account value.
    - **Total PnL (Profit and Loss):** The total profit or loss.
- It helps you understand how well your strategy performed.

## `data_loader.py`

This file is responsible for loading market data.

- It reads CSV files that contain price information (Open, High, Low, Close, Volume).
- It prepares the data so the backtesting engine can use it.
- You can specify which data series (files) to load.

## `plotting.py`

This file creates plots and charts to visualize the results.

- It can plot the equity curve, which shows how your account value changes over time.
- It can also create other useful charts, like underwater plots (to see drawdowns).
- Visualizing results makes it easier to understand a strategy's behavior.

## `strategies_loader.py`

This file is used to find and load trading strategies.

- It looks for strategy files in the `strategies` directory.
- It imports the strategy class from the file so the backtester can run it.
- This makes it easy to add new strategies without changing the main code.

## `strategy_base.py`

This file provides a base class for all trading strategies.

- It defines the basic structure that every strategy must follow.
- It includes methods like `on_bar` (called for each new price bar) and `on_order_update`.
- When you create a new strategy, you create a class that inherits from `StrategyBase`. This ensures your strategy will work with the backtesting engine.

## `scripts/make_dist.py`

This script is a tool to package the project into a clean ZIP file.

-   **Purpose:** To create a distributable version of the project for sharing or submission.
-   **What it does:**
    -   It copies all the important project files.
    -   It excludes unnecessary files and folders, such as Git history (`.git`), IDE settings (`.idea`), and Python cache files (`__pycache__`).
    -   It can optionally exclude the `output/` folder, which contains generated charts and results.
-   **How to use:** You run this script from your terminal to create the ZIP archive.

## Trading Strategies

This section describes the example trading strategies included in the `strategies/` directory.

### `template_strategy.py`
- **Purpose**: A starter template for creating new strategies.
- **Logic**: Shows a basic example of buying a fixed amount if there is no current position. It demonstrates how to use the framework's helper functions like `overspend_guard` and `place_market`.

### `example_buy_and_hold.py`
- **Purpose**: A simple demonstration strategy.
- **Logic**: Buys a fixed amount of a single instrument at the start of the test and holds it until the end.

### `fixed.py`
- **Purpose**: A static allocation strategy.
- **Logic**: On the first day, it buys or sells to reach a pre-defined fixed position size for each instrument and then holds these positions for the entire backtest.

### `copycat.py`
- **Purpose**: A simple daily momentum strategy.
- **Logic**: If the previous day's price went up (Close > Open), it takes a long position. If the price went down, it takes a short position.

### `sma_cross.py`
- **Purpose**: A classic trend-following strategy.
- **Logic**: Uses two Simple Moving Averages (SMA), one fast and one slow. It buys when the fast SMA crosses above the slow SMA and sells when it crosses below.

### Bollinger Bands Strategies
These strategies use Bollinger Bands, which are lines plotted at a standard deviation level above and below a simple moving average of the price.

-   **`p_bbands_contrarian.py`**: A mean-reversion strategy. It assumes prices will revert to the mean.
    -   **Logic**: Buys when the price hits the lower band and sells when it hits the upper band.

-   **`p_bbands_trend_following.py`**: A breakout (trend-following) strategy.
    -   **Logic**: Buys when the price breaks above the upper band and sells when it breaks below the lower band.

-   **`bbands_holding_period.py`**: A variation of the contrarian strategy with a time limit.
    -   **Logic**: Same as the contrarian strategy, but it will exit a position after a fixed number of days (`holdPeriod`), regardless of the price.

-   **`p_bbands_holding_period_diag.py`**: A diagnostic version of the holding period strategy with extra print logs for debugging.

### `p_RSI_contrarian.py`
- **Purpose**: A mean-reversion strategy using the Relative Strength Index (RSI).
- **Logic**: RSI measures if an asset is overbought or oversold. This strategy sells when RSI is high (overbought) and buys when RSI is low (oversold).

### Market Making & Limit Order Strategies

-   **`simple_limit.py`**: A market-making strategy.
    -   **Logic**: Places both a buy limit order and a sell limit order every day to try and capture the spread. It will flatten its position if it holds too much inventory.

-   **`p_mm_spread.py`**: A pseudo-market-making strategy.
    -   **Logic**: Similar to `simple_limit`, it places buy and sell limit orders daily based on the previous day's price range. It also has an inventory limit.

### High-Risk & Demonstration Strategies

-   **`p_short5_long5.py`**: An extreme, high-leverage strategy designed for 10 instruments.
    -   **Logic**: On Day 1, it shorts the first 5 instruments. On Day 2, it uses the remaining cash to go long on the other 5.

-   **`s_short_then_long.py`**: A single-instrument version of the above.
    -   **Logic**: Shorts the instrument on Day 1, then flips to a long position on Day 2.

-   **`p_bankrupt.py`**: A demonstration of a strategy likely to go bankrupt.
    -   **Logic**: Similar to `p_short5_long5`, but for any number of instruments (>=6). It shorts the first 5 and goes long on the rest.

-   **`p_big_spender.py`**: A strategy that constantly tries to trade.
    -   **Logic**: Every day, it attempts to place fixed-size market orders for all instruments, but only if a pre-trade check estimates it has enough cash.

-   **`p_random.py`**: A chaotic strategy for testing purposes.
    -   **Logic**: Places a market order with a random size for every instrument, every day.

## Testing

### `tests/test_rules.py`

This file contains automated tests to ensure the custom rules of the backtesting framework are working as expected.

-   **Purpose**: To verify the correctness of the framework's core logic.
-   **What it tests**:
    -   **Slippage**: Confirms that the correct slippage is applied to market orders, especially when there are price gaps.
    -   **Overspend Guard**: Checks that the framework prevents strategies from spending more cash than they have.
    -   **Liquidation**: Ensures that the "liquidate at end" policy correctly closes all positions on the final day.
    -   **Bankruptcy**: Verifies that the backtest halts correctly if a strategy loses all its money.
    -   **Order Cancellation**: Tests that if multiple orders are placed on the same day that would collectively overspend, all of them are cancelled.