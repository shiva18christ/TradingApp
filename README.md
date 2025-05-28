# Trade Simulator

A high-performance trade simulator that leverages real-time market data to estimate transaction costs and market impact for cryptocurrency trading.

## Overview

This application connects to OKX WebSocket endpoints to stream full L2 orderbook data and calculates various trading metrics in real-time, including:

- Expected slippage using quantile regression
- Expected fees based on exchange fee tiers
- Market impact using Almgren-Chriss model
- Net transaction costs
- Maker/Taker proportion prediction
- Processing latency measurements

## Installation

### Prerequisites

- Python 3.8+
- pip package manager

### Setup

1. Clone this repository
2. Create a virtual environment:
   ```
   python -m venv .venv
   ```
3. Activate the virtual environment:
   - Windows: `.venv\Scripts\activate`
   - Linux/Mac: `source .venv/bin/activate`
4. Install dependencies:
   ```
   pip install websockets numpy statsmodels scikit-learn
   ```

## Usage

Run the application:
```
python main.py
```

The UI consists of two main panels:
- Left panel: Input parameters for the trade simulation
- Right panel: Real-time output metrics and orderbook visualization

## Architecture

The application is structured with the following components:

- `main.py`: Entry point that initializes the application and manages threading
- `models.py`: Contains models for calculating slippage, fees, and market impact
- `websocket_client.py`: Handles WebSocket connection and data processing
- `ui.py`: Implements the Tkinter-based user interface

## Model Implementation

### Slippage Model

The slippage model uses quantile regression to estimate the expected slippage based on the order book depth:

```python
def calculate_expected_slippage(self, order_book):
    """Quantile regression-based slippage estimation."""
    try:
        bids = np.array([(float(p), float(v)) for p, v in order_book['bids']])
        if len(bids) == 0:
            return 0.0

        X = bids[:, 1].reshape(-1, 1)  # Volume as feature
        y = bids[:, 0]  # Price levels
        model = QuantReg(y, X).fit(q=0.5)
        return abs(model.predict([self.order_size])[0] - bids[0, 0]) / bids[0, 0]
    except Exception:
        return 0.0
```

### Market Impact Model

The market impact model implements the Almgren-Chriss approach, which separates market impact into temporary and permanent components:

```python
def calculate_market_impact(self, order_size, order_book):
    """Enhanced Almgren-Chriss with permanent/temporary impact."""
    try:
        best_ask = float(order_book['asks'][0][0])
        best_bid = float(order_book['bids'][0][0])
        spread = best_ask - best_bid

        # Temporary impact (instantaneous)
        temp_impact = self.impact_coefficient * (order_size ** 1.5) * spread / best_ask
        # Permanent impact (simplified)
        perm_impact = 0.3 * temp_impact
        return temp_impact + perm_impact
    except Exception:
        return 0.0
```

### Maker/Taker Proportion Prediction

The application uses logistic regression to predict the maker/taker proportion based on order book features:

```python
def _calculate_maker_taker(self, bids, asks):
    """Logistic regression classifier for maker/taker."""
    if not bids or not asks:
        return "0%", "0%"

    try:
        bids = np.array([(float(p), float(v)) for p, v in bids])
        asks = np.array([(float(p), float(v)) for p, v in asks])
        mid_price = (bids[0, 0] + asks[0, 0]) / 2

        # Features: [price_distance_from_mid, log_volume]
        X = np.vstack([
            np.column_stack([bids[:, 0] - mid_price, np.log(bids[:, 1])]),
            np.column_stack([asks[:, 0] - mid_price, np.log(asks[:, 1])])
        ])
        # Labels: 1=maker (near mid), 0=taker (aggressive)
        y = np.concatenate([
            np.ones(len(bids)),  # Bids are makers
            np.zeros(len(asks))  # Asks are takers (for market buys)
        ])

        model = LogisticRegression()
        model.fit(X, y)
        maker_prop = model.predict_proba(X)[:, 1].mean() * 100
        return f"{maker_prop:.1f}%", f"{100 - maker_prop:.1f}%"
    except Exception:
        return "0%", "0%"
```

## Performance Optimization

### Latency Measurement

The application measures and displays two types of latency:
- Processing latency: Time taken to process each orderbook update
- Total latency: End-to-end time including network communication

### Memory Management

The application uses NumPy arrays for efficient numerical computations and memory usage.

### Thread Management

The application uses a multi-threaded architecture:
- Main thread: UI rendering and user interaction
- Background thread: WebSocket communication and data processing

