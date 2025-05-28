import asyncio
import tkinter as tk
from websocket_client import WebSocketClient
from ui import TradeSimulatorUI
import threading
import logging
import sys
import signal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("trade_simulator.log")
    ]
)
logger = logging.getLogger("Main")


class Application:
    def __init__(self):
        logger.info("Initializing application")
        self.root = tk.Tk()
        self.root.title("Trade Simulator")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Create UI
        self.ui = TradeSimulatorUI(self.root)
        
        # Setup asyncio event loop
        self.loop = asyncio.new_event_loop()
        
        # Create WebSocket client
        self.ws_client = WebSocketClient(ui_callback=self.ui.update_display)
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        logger.info("Application initialized")

    def start_websocket(self):
        """Start WebSocket client in a separate thread"""
        def run_loop(loop):
            asyncio.set_event_loop(loop)
            try:
                loop.run_forever()
            except Exception as e:
                logger.error(f"Event loop error: {str(e)}")
            finally:
                logger.info("Event loop stopped")

        # Start WebSocket in separate thread
        self.ws_thread = threading.Thread(
            target=run_loop,
            args=(self.loop,),
            daemon=True
        )
        self.ws_thread.start()
        logger.info("WebSocket thread started")

        # Schedule WebSocket connection
        asyncio.run_coroutine_threadsafe(
            self.ws_client.run(),
            self.loop
        )

    def run(self):
        """Run the application"""
        try:
            logger.info("Starting application")
            self.start_websocket()
            self.root.mainloop()
        except Exception as e:
            logger.critical(f"Application error: {str(e)}")
            sys.exit(1)
        finally:
            self.cleanup()

    def on_closing(self):
        """Handle window close event"""
        logger.info("Application closing")
        self.cleanup()
        self.root.destroy()
        sys.exit(0)

    def signal_handler(self, sig, frame):
        """Handle termination signals"""
        logger.info(f"Received signal {sig}, shutting down")
        self.cleanup()
        sys.exit(0)

    def cleanup(self):
        """Clean up resources"""
        logger.info("Cleaning up resources")
        # Stop WebSocket client
        self.ws_client.running = False
        # Stop event loop
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)
        logger.info("Cleanup complete")


if __name__ == "__main__":
    try:
        app = Application()
        app.run()
    except Exception as e:
        logger.critical(f"Unhandled exception: {str(e)}")
        sys.exit(1)