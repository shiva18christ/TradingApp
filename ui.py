import tkinter as tk
from tkinter import ttk
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("UI")


class TradeSimulatorUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Trade Simulator")
        self.root.geometry("1000x700")  # Increased size for more metrics
        
        # Configure styles
        self.setup_styles()
        
        # Create main frames
        self.create_frames()
        
        # Setup input panel
        self.setup_input_panel()
        
        # Setup output panel
        self.setup_output_panel()
        
        # Setup orderbook display
        self.setup_orderbook_display()
        
        # Setup performance metrics panel
        self.setup_performance_panel()
        
        # Setup status bar
        self.setup_status_bar()
        
        logger.info("UI initialized")

    def setup_styles(self):
        """Configure UI styles"""
        self.style = ttk.Style()
        self.style.configure('TLabel', font=('Arial', 10))
        self.style.configure('Header.TLabel', font=('Arial', 12, 'bold'))
        self.style.configure('Value.TLabel', font=('Arial', 10))
        self.style.configure('Status.TLabel', font=('Arial', 9), foreground='gray')
        self.style.configure('Error.TLabel', foreground='red')
        self.style.configure('Success.TLabel', foreground='green')

    def create_frames(self):
        """Create main UI frames"""
        # Main container frame
        self.main_frame = ttk.Frame(self.root, padding=5)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Input Panel
        self.input_frame = ttk.LabelFrame(self.main_frame, text="Trade Parameters", padding=10)
        self.input_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        # Right side container
        self.right_frame = ttk.Frame(self.main_frame)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Output Panel
        self.output_frame = ttk.LabelFrame(self.right_frame, text="Transaction Costs", padding=10)
        self.output_frame.pack(fill=tk.X, pady=5)
        
        # Performance Panel
        self.perf_frame = ttk.LabelFrame(self.right_frame, text="Performance Metrics", padding=10)
        self.perf_frame.pack(fill=tk.X, pady=5)
        
        # Orderbook Panel
        self.orderbook_frame = ttk.LabelFrame(self.right_frame, text="Order Book", padding=10)
        self.orderbook_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Status bar
        self.status_frame = ttk.Frame(self.root, padding=2)
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X)

    def setup_input_panel(self):
        """Setup input parameters panel"""
        self.vars = {}
        params = [
            ("Exchange:", "OKX", True),
            ("Spot Asset:", "BTC-USDT-SWAP", False),
            ("Order Type:", "Market", True),
            ("Quantity (USD):", "100", False),
            ("Fee Tier:", "0.1% (Taker)", True),
            ("Volatility (%):", "2.0", False)
        ]

        for label, default, readonly in params:
            frame = ttk.Frame(self.input_frame)
            frame.pack(fill=tk.X, pady=2)
            ttk.Label(frame, text=label, width=15).pack(side=tk.LEFT)
            var = tk.StringVar(value=default)
            entry = ttk.Entry(frame, textvariable=var, state='readonly' if readonly else 'normal')
            entry.pack(side=tk.RIGHT, expand=True)
            self.vars[label.strip(':').lower().replace(' ', '_')] = var

    def setup_output_panel(self):
        """Setup output metrics panel"""
        metrics = [
            ("Volatility:", "volatility"),
            ("Expected Slippage:", "slippage"),
            ("Expected Fees:", "fees"),
            ("Market Impact:", "impact"),
            ("Net Cost:", "net_cost"),
            ("Maker Proportion:", "maker_proportion"),
            ("Taker Proportion:", "taker_proportion")
        ]

        self.output_vars = {}
        for i, (label, key) in enumerate(metrics):
            row = i // 2
            col = (i % 2) * 2
            
            ttk.Label(self.output_frame, text=label).grid(row=row, column=col, sticky=tk.W, padx=5, pady=2)
            var = tk.StringVar(value="-")
            ttk.Label(self.output_frame, textvariable=var, style='Value.TLabel').grid(row=row, column=col+1, sticky=tk.W, padx=5)
            self.output_vars[key] = var
            
        # Configure grid
        for i in range(4):
            self.output_frame.columnconfigure(i, weight=1)

    def setup_performance_panel(self):
        """Setup performance metrics panel"""
        metrics = [
            ("Processing Latency:", "processing_latency"),
            ("Total Latency:", "total_latency"),
            ("Average Latency:", "avg_latency"),
            ("Connection Status:", "status")
        ]

        self.perf_vars = {}
        for i, (label, key) in enumerate(metrics):
            row = i // 2
            col = (i % 2) * 2
            
            ttk.Label(self.perf_frame, text=label).grid(row=row, column=col, sticky=tk.W, padx=5, pady=2)
            var = tk.StringVar(value="-")
            ttk.Label(self.perf_frame, textvariable=var, style='Value.TLabel').grid(row=row, column=col+1, sticky=tk.W, padx=5)
            self.perf_vars[key] = var
            
        # Configure grid
        for i in range(4):
            self.perf_frame.columnconfigure(i, weight=1)

    def setup_orderbook_display(self):
        """Setup orderbook display"""
        # Create headers
        header_frame = ttk.Frame(self.orderbook_frame)
        header_frame.pack(fill=tk.X)
        
        ttk.Label(header_frame, text="Price", width=12).pack(side=tk.LEFT, padx=5)
        ttk.Label(header_frame, text="Volume", width=12).pack(side=tk.LEFT, padx=5)
        ttk.Label(header_frame, text="", width=5).pack(side=tk.LEFT)
        ttk.Label(header_frame, text="Price", width=12).pack(side=tk.LEFT, padx=5)
        ttk.Label(header_frame, text="Volume", width=12).pack(side=tk.LEFT, padx=5)
        
        # Orderbook text display
        self.orderbook_text = tk.Text(self.orderbook_frame, height=15, width=60, font=('Courier', 10))
        self.orderbook_text.pack(fill=tk.BOTH, expand=True, pady=5)
        self.orderbook_text.config(state='disabled')
        
        # Add timestamp display
        self.timestamp_var = tk.StringVar(value="Last update: -")
        ttk.Label(self.orderbook_frame, textvariable=self.timestamp_var, style='Status.TLabel').pack(anchor=tk.E)

    def setup_status_bar(self):
        """Setup status bar at bottom of window"""
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(self.status_frame, textvariable=self.status_var, style='Status.TLabel')
        self.status_label.pack(side=tk.LEFT, padx=5)

    def update_display(self, data):
        """Schedule UI update on main thread"""
        self.root.after(0, lambda: self._update_display(data))

    def _update_display(self, data):
        """Update UI with new data"""
        try:
            if isinstance(data, dict):
                # Update output metrics
                for key, var in self.output_vars.items():
                    if key in data:
                        var.set(data[key])
                
                # Update performance metrics
                for key, var in self.perf_vars.items():
                    if key in data:
                        var.set(data[key])
                
                # Update orderbook
                if 'bids' in data and 'asks' in data:
                    self._update_orderbook(data)
                    
                # Update timestamp
                if 'timestamp' in data:
                    self.timestamp_var.set(f"Last update: {data['timestamp']}")
                    
                # Update status
                if 'status' in data:
                    self.status_var.set(data['status'])
                    self.status_label.configure(style='Success.TLabel')
                elif 'error' in data:
                    self.status_var.set(f"Error: {data['error']}")
                    self.status_label.configure(style='Error.TLabel')
        except Exception as e:
            logger.error(f"UI update error: {e}")
            self.status_var.set(f"UI Error: {str(e)}")
            self.status_label.configure(style='Error.TLabel')

    def _update_orderbook(self, data):
        """Update orderbook display"""
        try:
            self.orderbook_text.config(state='normal')
            self.orderbook_text.delete(1.0, tk.END)
            
            # Format and display bids and asks
            bids = sorted([(float(p), float(v)) for p, v in data['bids'][:5]], reverse=True)
            asks = sorted([(float(p), float(v)) for p, v in data['asks'][:5]])
            
            # Create a formatted display with colors
            text = ""
            for i in range(max(len(bids), len(asks))):
                if i < len(bids):
                    bid_price, bid_vol = bids[i]
                    text += f"{bid_price:>10.2f} {bid_vol:>10.4f}  |  "
                else:
                    text += " " * 23 + "|  "
                    
                if i < len(asks):
                    ask_price, ask_vol = asks[i]
                    text += f"{ask_price:<10.2f} {ask_vol:<10.4f}\n"
                else:
                    text += "\n"
            
            self.orderbook_text.insert(tk.END, text)
            
            # Apply colors (green for bids, red for asks)
            lines = text.split('\n')
            for i, line in enumerate(lines):
                if '|' in line:
                    bid_end = line.find('|')
                    if bid_end > 0:
                        self.orderbook_text.tag_add("bid", f"{i+1}.0", f"{i+1}.{bid_end}")
                    if bid_end < len(line):
                        self.orderbook_text.tag_add("ask", f"{i+1}.{bid_end+1}", f"{i+1}.end")
            
            self.orderbook_text.tag_config("bid", foreground="green")
            self.orderbook_text.tag_config("ask", foreground="red")
            self.orderbook_text.config(state='disabled')
        except Exception as e:
            logger.error(f"Orderbook update error: {e}")