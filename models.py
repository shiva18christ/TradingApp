import numpy as np
from statsmodels.regression.quantile_regression import QuantReg
import logging
from functools import lru_cache

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Models")


class SlippageModel:
    def __init__(self, volatility=0.02, order_size=100):
        self.volatility = volatility
        self.order_size = order_size
        self.last_slippage = 0.0
        logger.info(f"SlippageModel initialized with volatility={volatility}, order_size={order_size}")

    @lru_cache(maxsize=32)
    def _cached_slippage_calculation(self, bid_tuple):
        """Cached version of slippage calculation for similar orderbooks."""
        try:
            bids = np.array(bid_tuple)
            if len(bids) == 0:
                return 0.0

            X = bids[:, 1].reshape(-1, 1)  # Volume as feature
            y = bids[:, 0]  # Price levels
            
            # Use robust model fitting with error handling
            try:
                model = QuantReg(y, X).fit(q=0.5)
                predicted_price = model.predict([self.order_size])[0]
                best_bid = bids[0, 0]
                return abs(predicted_price - best_bid) / best_bid
            except Exception as e:
                logger.warning(f"Quantile regression failed: {str(e)}. Using fallback calculation.")
                # Fallback to simpler calculation if regression fails
                return self.volatility * (self.order_size / bids[:, 1].sum()) * 0.1
        except Exception as e:
            logger.error(f"Error in cached slippage calculation: {str(e)}")
            return self.last_slippage or 0.0

    def calculate_expected_slippage(self, order_book):
        """Quantile regression-based slippage estimation."""
        try:
            if not order_book or 'bids' not in order_book or not order_book['bids']:
                return self.last_slippage or 0.0
                
            # Convert to numpy arrays
            bids_array = np.array([(float(p), float(v)) for p, v in order_book['bids']])
            
            # Convert to hashable format for caching
            bid_tuple = tuple(map(tuple, bids_array))
            
            # Use cached calculation
            slippage = self._cached_slippage_calculation(bid_tuple)
            self.last_slippage = slippage
            return slippage
        except Exception as e:
            logger.error(f"Slippage calculation error: {str(e)}")
            return self.last_slippage or 0.0


class FeeModel:
    def __init__(self, fee_tier=0.001):
        self.fee_tier = fee_tier
        logger.info(f"FeeModel initialized with fee_tier={fee_tier}")

    def calculate_expected_fees(self, order_size, price):
        try:
            return self.fee_tier * order_size * price
        except Exception as e:
            logger.error(f"Fee calculation error: {str(e)}")
            return 0.0


class MarketImpactModel:
    def __init__(self, impact_coefficient=0.1):
        self.impact_coefficient = impact_coefficient
        self.last_impact = 0.0
        logger.info(f"MarketImpactModel initialized with impact_coefficient={impact_coefficient}")

    @lru_cache(maxsize=32)
    def _cached_impact_calculation(self, order_size, best_ask, best_bid):
        """Cached version of market impact calculation."""
        try:
            spread = best_ask - best_bid
            
            # Temporary impact (instantaneous)
            temp_impact = self.impact_coefficient * (order_size ** 1.5) * spread / best_ask
            # Permanent impact (simplified)
            perm_impact = 0.3 * temp_impact
            return temp_impact + perm_impact
        except Exception as e:
            logger.error(f"Error in cached impact calculation: {str(e)}")
            return self.last_impact or 0.0

    def calculate_market_impact(self, order_size, order_book):
        """Enhanced Almgren-Chriss with permanent/temporary impact."""
        try:
            if not order_book or 'asks' not in order_book or not order_book['asks'] or 'bids' not in order_book or not order_book['bids']:
                return self.last_impact or 0.0
                
            best_ask = float(order_book['asks'][0][0])
            best_bid = float(order_book['bids'][0][0])
            
            # Use cached calculation
            impact = self._cached_impact_calculation(order_size, best_ask, best_bid)
            self.last_impact = impact
            return impact
        except Exception as e:
            logger.error(f"Market impact calculation error: {str(e)}")
            return self.last_impact or 0.0


class TradeCostCalculator:
    def __init__(self, slippage_model, fee_model, impact_model):
        self.slippage_model = slippage_model
        self.fee_model = fee_model
        self.impact_model = impact_model
        self.last_cost = {'slippage': 0, 'fees': 0, 'impact': 0, 'net_cost': 0}
        logger.info("TradeCostCalculator initialized")

    def calculate_total_cost(self, usd_quantity, order_book):
        try:
            if not order_book or 'asks' not in order_book or not order_book['asks']:
                logger.warning("Invalid order book data for cost calculation")
                return self.last_cost
                
            best_ask = float(order_book['asks'][0][0])
            order_size = usd_quantity / best_ask
            
            # Calculate components
            slippage = self.slippage_model.calculate_expected_slippage(order_book)
            fees = self.fee_model.calculate_expected_fees(order_size, best_ask)
            impact = self.impact_model.calculate_market_impact(order_size, order_book)
            
            # Calculate net cost
            result = {
                'slippage': slippage,
                'fees': fees,
                'impact': impact,
                'net_cost': slippage + fees + impact
            }
            
            self.last_cost = result
            return result
        except Exception as e:
            logger.error(f"Total cost calculation error: {str(e)}")
            return self.last_cost