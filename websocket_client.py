import asyncio
import websockets
import json
import logging
import numpy as np
from datetime import datetime
from sklearn.linear_model import LogisticRegression
from models import TradeCostCalculator, SlippageModel, FeeModel, MarketImpactModel
import time
from functools import lru_cache

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("WebSocketClient")

WS_URL = "wss://ws.gomarket-cpp.goquant.io/ws/l2-orderbook/okx/BTC-USDT-SWAP"


class WebSocketClient:
    def __init__(self, ui_callback):
        self.ui_callback = ui_callback
        self.running = False
        self.retry_count = 0
        self.max_retries = 5
        self.retry_delay = 5
        self.latencies = []
        self.message_count = 0
        self.last_model_update = 0
        self.model_update_interval = 5  # seconds
        self.logistic_model = None

        # Initialize models
        self.slippage_model = SlippageModel(volatility=0.02, order_size=100)
        self.fee_model = FeeModel(fee_tier=0.001)
        self.impact_model = MarketImpactModel(impact_coefficient=0.1)
        self.cost_calculator = TradeCostCalculator(
            self.slippage_model, self.fee_model, self.impact_model
        )

        # Performance metrics
        self.avg_processing_time = 0
        self.max_processing_time = 0
        self.min_processing_time = float('inf')
        
        logger.info("WebSocket client initialized")

    @lru_cache(maxsize=32)
    def _cached_maker_taker_calculation(self, bid_tuple, ask_tuple):
        """Cached version of maker/taker calculation for similar orderbooks."""
        # Convert tuples back to arrays for processing
        bids = np.array(bid_tuple)
        asks = np.array(ask_tuple)
        
        if len(bids) == 0 or len(asks) == 0:
            return "0%", "0%"
            
        try:
            mid_price = (bids[0, 0] + asks[0, 0]) / 2

            # Features: [price_distance_from_mid, log_volume]
            X = np.vstack([
                np.column_stack([bids[:, 0] - mid_price, np.log(np.maximum(bids[:, 1], 0.001))]),
                np.column_stack([asks[:, 0] - mid_price, np.log(np.maximum(asks[:, 1], 0.001))])
            ])
            # Labels: 1=maker (near mid), 0=taker (aggressive)
            y = np.concatenate([
                np.ones(len(bids)),  # Bids are makers
                np.zeros(len(asks))  # Asks are takers (for market buys)
            ])

            # Only retrain model periodically to save CPU
            current_time = time.time()
            if self.logistic_model is None or (current_time - self.last_model_update > self.model_update_interval):
                self.logistic_model = LogisticRegression(warm_start=True)
                self.logistic_model.fit(X, y)
                self.last_model_update = current_time
                
            maker_prop = self.logistic_model.predict_proba(X)[:, 1].mean() * 100
            return f"{maker_prop:.1f}%", f"{100 - maker_prop:.1f}%"
        except Exception as e:
            logger.error(f"Error in maker/taker calculation: {str(e)}")
            return "0%", "0%"

    def _calculate_maker_taker(self, bids, asks):
        """Logistic regression classifier for maker/taker."""
        if not bids or not asks:
            return "0%", "0%"

        try:
            # Convert to numpy arrays for processing
            bids_array = np.array([(float(p), float(v)) for p, v in bids])
            asks_array = np.array([(float(p), float(v)) for p, v in asks])
            
            # Convert to hashable format for caching
            bid_tuple = tuple(map(tuple, bids_array))
            ask_tuple = tuple(map(tuple, asks_array))
            
            # Use cached calculation if available
            return self._cached_maker_taker_calculation(bid_tuple, ask_tuple)
            
        except Exception as e:
            logger.error(f"Error preparing data for maker/taker calculation: {str(e)}")
            return "0%", "0%"

    async def run(self):
        self.running = True
        while self.running and self.retry_count < self.max_retries:
            try:
                logger.info(f"Connecting to WebSocket at {WS_URL}")
                async with websockets.connect(WS_URL) as websocket:
                    self.retry_count = 0
                    self.ui_callback({"status": "Connected"})
                    logger.info("WebSocket connection established")

                    while self.running:
                        try:
                            start_time = datetime.now()
                            message = await asyncio.wait_for(websocket.recv(), timeout=10)
                            processing_start = datetime.now()

                            data = json.loads(message)
                            result = self.process_orderbook(data)
                            self.message_count += 1

                            # Latency tracking
                            processing_ms = (datetime.now() - processing_start).total_seconds() * 1000
                            total_ms = (datetime.now() - start_time).total_seconds() * 1000
                            
                            # Update performance metrics
                            self.avg_processing_time = (self.avg_processing_time * (self.message_count - 1) + processing_ms) / self.message_count
                            self.max_processing_time = max(self.max_processing_time, processing_ms)
                            self.min_processing_time = min(self.min_processing_time, processing_ms)
                            
                            result.update({
                                "processing_latency": f"{processing_ms:.2f}ms",
                                "total_latency": f"{total_ms:.2f}ms",
                                "avg_latency": f"{self.avg_processing_time:.2f}ms"
                            })
                            self.ui_callback(result)
                            
                            # Log performance every 100 messages
                            if self.message_count % 100 == 0:
                                logger.info(f"Performance: Avg={self.avg_processing_time:.2f}ms, Min={self.min_processing_time:.2f}ms, Max={self.max_processing_time:.2f}ms")
                                
                        except asyncio.TimeoutError:
                            logger.warning("WebSocket timeout, reconnecting...")
                            break
                        except json.JSONDecodeError as e:
                            logger.error(f"JSON decode error: {str(e)}")
                            continue

            except Exception as e:
                self.retry_count += 1
                error_msg = f"Connection failed (attempt {self.retry_count}/{self.max_retries}): {str(e)}"
                logger.error(error_msg)
                self.ui_callback({"error": error_msg})
                await asyncio.sleep(self.retry_delay)

        if self.retry_count >= self.max_retries:
            logger.critical("Maximum retry attempts reached. Giving up.")

    def process_orderbook(self, data):
        try:
            # Pre-validate data to avoid unnecessary processing
            if not data or 'bids' not in data or 'asks' not in data:
                logger.warning("Received invalid orderbook data")
                return {'error': 'Invalid orderbook data'}
                
            cost_data = self.cost_calculator.calculate_total_cost(100, data)
            maker_prop, taker_prop = self._calculate_maker_taker(data.get('bids', []), data.get('asks', []))

            return {
                'timestamp': datetime.now().strftime("%H:%M:%S.%f")[:-3],
                'slippage': f"{cost_data['slippage']:.6f}",
                'fees': f"${cost_data['fees']:.4f}",
                'impact': f"{cost_data['impact']:.6f}",
                'net_cost': f"${cost_data['slippage'] + cost_data['fees'] + cost_data['impact']:.4f}",
                'maker_proportion': maker_prop,
                'taker_proportion': taker_prop,
                'bids': data['bids'][:5],
                'asks': data['asks'][:5],
                'volatility': f"{self.slippage_model.volatility * 100:.2f}%"
            }
        except Exception as e:
            logger.error(f"Processing error: {e}")
            return {'error': str(e)}