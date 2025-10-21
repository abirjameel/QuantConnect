# region imports
from AlgorithmImports import *
from datetime import timedelta
# endregion

class PositionManagementAlgorithm(QCAlgorithm):

    def initialize(self):
        self.set_start_date(2025, 1, 1)
        self.set_end_date(2025, 3, 31)
        self.set_cash(1000000)
        self._symbol = None
        self._future_chain = self.add_future(Futures.Indices.SP_500_E_MINI, Resolution.DAILY)
        self._future_chain.set_filter(self.FutureFilter)
        self.escontinuos_symbol = self._future_chain.symbol
        
        self._sma = SimpleMovingAverage(50)
        self._atr = self.atr(self.escontinuos_symbol, 14, MovingAverageType.SIMPLE)
        self.set_warm_up(timedelta(days=5))
        # Pyramiding parameters
        self.pyramid_percent_move = 0.01 # 1% price move to add position
        self.max_pyramid_levels = 4  # Maximum number of additions
        self.scaling_factor = 0.5  # Each addition is 50% of previous
        self.min_profit_for_add = 1.5  # Add when profit >= 1.5 * ATR
        self.max_total_position_risk = 0.08  # Max 8% total portfolio risk
        # Track pyramiding information
        self.pyramid_entries = []  # List of dicts: {'price': X, 'quantity': Y}
        self.current_stop_ticket = None
        self.last_entry_price = 0

    def FutureFilter(self, universe: FutureFilterUniverse):
        # Filter for contracts expiring in quarter
        return universe.expiration_cycle([3,6,9,12])


    def on_data(self, data: Slice):
        if self.is_warming_up:
            self.log("### Warming Up...")
            return
            
        self._symbol = self.securities[self.escontinuos_symbol].mapped
        try:
            bar = data.bars[self._symbol]

            current_price = bar.close
        except Exception as e:
            self.debug(e)
            return 
        self._sma.update(bar.end_time, bar.close)
        
        
        # Entry logic - first position
        if not self.portfolio.invested:
            quantity = self.calculate_order_quantity(self._symbol, target=0.5)
            self.last_target = 0.5
            if quantity <=0:
                quantity = 1
            total_value = quantity * current_price
            self.market_order(self._symbol, quantity)
            
            # Track entry
            self.pyramid_entries.append({
                'price': current_price,
                'quantity': quantity
            })
            self.last_entry_price = current_price
            
            # Set initial stop loss 
            risk_amount = total_value * self.max_total_position_risk

            # Stop price = Entry price - Risk per share
            stop_price = current_price - round(risk_amount / quantity, 2)
            self.current_stop_ticket = self.stop_market_order(
                self._symbol, 
                -quantity, 
                stop_price
            )
            
        # Pyramiding logic - add to position
        elif len(self.pyramid_entries) < self.max_pyramid_levels:
            # Check if price moved favorably by threshold percentage
            price_move_percent = (current_price - self.last_entry_price) / self.last_entry_price
            
            if price_move_percent >= self.pyramid_percent_move:
                # Calculate position size for this level
                new_target = round(self.last_target * self.scaling_factor, 2)
                quantity = self.calculate_order_quantity(self._symbol, new_target)
                if quantity <= 0:
                    quantity = 1
                self.market_order(self._symbol, quantity)
                self.log(f"Adding Positions- new_target: {new_target}, quantity: {quantity}")
                # Track new entry
                self.pyramid_entries.append({
                    'price': current_price,
                    'quantity': quantity
                })
                self.last_entry_price = current_price
                self.last_target = new_target
                # Update stop loss to protect gains
                self.update_stop_loss()


    def update_stop_loss(self):
        """Update stop loss based on pyramiding entries"""
        # Calculate average entry price
        total_value = sum(e['price'] * e['quantity'] for e in self.pyramid_entries)
        total_quantity = sum(e['quantity'] for e in self.pyramid_entries)
        avg_entry_price = total_value / total_quantity
        avg_entry_price_1 = self.portfolio[self._symbol].average_price
        
        
        # portfolio_value = self.portfolio.total_holdings_value
        risk_amount = total_value * self.max_total_position_risk
        
        # Calculate price distance per contract
        risk_per_contrct = round(risk_amount / total_quantity, 2)
        
        # Stop price = Entry price - Risk per share
        updated_stop_price = avg_entry_price - risk_per_contrct
        self.log(f"avg_entry_price: {avg_entry_price} and avg_entry_price_1: {avg_entry_price_1}, updated_stop_price: {updated_stop_price}")
        # Cancel existing stop loss
        if self.current_stop_ticket and self.current_stop_ticket.status != OrderStatus.FILLED:
            self.current_stop_ticket.Cancel()
        
        # Place new stop loss for total position
        self.current_stop_ticket = self.stop_market_order(
            self._symbol,
            -total_quantity,
            updated_stop_price
        )
        
        # self.log(f"Updated stop loss to {updated_stop_price} for {total_quantity} contracts")

    def on_order_event(self, orderEvent: OrderEvent):
        """Handle order fills and track position changes"""
        if orderEvent.status != OrderStatus.FILLED:
            return
            
        # If stop loss was hit, reset positions information
        if self.current_stop_ticket and orderEvent.order_id == self.current_stop_ticket.order_id:
            self.pyramid_entries = []
            self.last_entry_price = 0
            self.last_target = 0
            self.current_stop_ticket = None
            self.log(f"Stop loss hit at {orderEvent.fill_price}")