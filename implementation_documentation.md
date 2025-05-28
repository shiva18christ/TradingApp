# Trade Simulator: Implementation Documentation

## Code Architecture

The application follows a modular design with clear separation of concerns:

### Core Components

1. **`main.py`**: 
   - Entry point that initializes the application
   - Coordinates threading between UI and data processing
   - Sets up logging and configuration

2. **`websocket_client.py`**: 
   - Handles WebSocket connection to OKX exchange
   - Processes raw L2 orderbook data
   - Implements reconnection logic and error handling
   - Passes processed data to models and UI components

3. **`models.py`**: 
   - Contains all analytical models:
     - Slippage estimation
     - Market impact calculation
     - Fee tier logic
     - Maker/Taker proportion prediction
   - Implements statistical regression techniques

4. **`ui.py`**: 
   - Implements the Tkinter-based user interface
   - Handles user inputs and updates output displays
   - Renders the orderbook visualization
   - Updates in real-time with each new orderbook tick

### Data Flow

1. WebSocket client receives orderbook data from OKX
2. Data is validated and preprocessed
3. Models calculate trading metrics based on orderbook state
4. UI is updated with results
5. Latency metrics are captured throughout the process

## Model Implementation Details

### Slippage Model

The slippage estimation model uses quantile regression to predict expected slippage based on the current orderbook state:

#### Algorithm Selection Rationale
Quantile regression was chosen over standard linear regression because:
- It provides more robust estimates in the presence of outliers
- It can better capture the asymmetric nature of orderbook depth
- It allows estimation at different quantiles (we use 0.5 for median expectation)

#### Implementation Details
The model:
1. Extracts price and volume data from the orderbook
2. Uses volume as the feature (X) and price levels as the target (y)
3. Fits a quantile regression model with q=0.5 (median)
4. Predicts the expected execution price for the given order size
5. Calculates slippage as the percentage difference from the best available price

This approach provides more accurate slippage estimates than simple linear interpolation, especially during volatile market conditions.

### Market Impact Model

The market impact model implements the Almgren-Chriss approach with enhancements for cryptocurrency markets:

#### Algorithm Selection Rationale
Almgren-Chriss was selected because:
- It separates market impact into temporary and permanent components
- It has strong theoretical foundations in market microstructure
- It can be calibrated to different market conditions

#### Implementation Details
The implementation:
1. Calculates bid-ask spread as a baseline for market liquidity
2. Computes temporary impact as a function of order size, spread, and an impact coefficient
3. Estimates permanent impact as a proportion of temporary impact
4. Combines both components for total market impact
5. Scales the result based on market volatility

Enhancements to the standard model include:
- Dynamic impact coefficient based on recent volatility
- Non-linear scaling with order size (using power law with exponent 1.5)
- Adjustments for cryptocurrency-specific market dynamics

### Fee Model

The fee calculation model uses a rule-based approach based on exchange fee tiers:

#### Algorithm Selection Rationale
A rule-based approach was chosen because:
- Exchange fee structures are deterministic
- Fees depend on specific tier levels rather than statistical patterns
- This approach provides exact fee calculations without approximation errors

#### Implementation Details
The model:
1. Maps user-selected fee tier to the appropriate maker and taker fee rates
2. Uses the maker/taker proportion prediction to weight the fee rates
3. Calculates expected fees based on order size and current asset price
4. Accounts for any exchange-specific fee discounts (e.g., for token holders)

### Maker/Taker Proportion Prediction

The model uses logistic regression to predict the likelihood of an order executing as maker vs. taker:

#### Algorithm Selection Rationale
Logistic regression was selected because:
- It provides probability estimates rather than just classifications
- It handles the binary nature of the maker/taker decision
- It performs well with limited features
- It's computationally efficient for real-time updates

#### Implementation Details
The implementation:
1. Extracts features from the orderbook:
   - Price distance from mid price
   - Logarithm of volume at each level
2. Creates training data with labels (1=maker, 0=taker)
3. Fits a logistic regression model
4. Predicts probability of maker execution
5. Returns maker/taker percentages based on the prediction

## Technical Implementation Highlights

### Real-time Processing
- Optimized data structures for minimal processing overhead
- Efficient algorithms that complete before next tick arrives
- Prioritization of critical calculations over non-essential ones

### Error Handling
- Comprehensive exception handling throughout the codebase
- Fallback mechanisms for calculation failures
- Logging of errors with appropriate context for debugging

### State Management
- Clean management of application state
- Proper initialization and cleanup procedures
- Thread-safe access to shared data structures

## UI Design Considerations

The UI was designed with the following principles:
1. Clear separation of inputs and outputs
2. Real-time visualization of key metrics
3. Intuitive parameter adjustment
4. Visual feedback on calculation accuracy and latency

Input controls were selected to balance ease of use with precision:
- Dropdown menus for categorical selections (exchange, asset)
- Sliders for continuous parameters with reasonable defaults
- Text inputs for precise numerical entries

Output displays feature:
- Color coding for positive/negative metrics
- Real-time updates with smooth transitions
- Historical trend visualization where appropriate
- Clear labeling and units for all metrics

## Model Validation Approach

Models were validated through:
1. Back-testing against historical orderbook data
2. Comparison with theoretical expectations
3. Stress testing with extreme market conditions
4. Consistency checks across different assets and time periods

## Technical Debt and Future Improvements

Areas identified for future enhancement:
1. Implementation of more sophisticated market impact models (e.g., Kyle-Obizhaeva)
2. Addition of historical data analysis for parameter calibration
3. Integration with additional exchanges for cross-market comparisons
4. Enhanced visualization options for orderbook dynamics 