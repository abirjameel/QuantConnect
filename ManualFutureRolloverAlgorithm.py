# region imports
from AlgorithmImports import *
from datetime import timedelta
# end region


class ManualFutureRolloverAlgorithm(QCAlgorithm):
    def Initialize(self):
        self.set_start_date(2025, 1, 1)
        self.set_end_date(2025, 12, 10)
        self.set_cash(100000)

        self._future_chain = self.add_future(Futures.Indices.SP_500_E_MINI, Resolution.DAILY)
        self._future_chain.set_filter(self.FutureFilter)
        self.es_symbol = self._future_chain.symbol
        self.active_contract = None
        self.next_rollover_date = None
        self._sma = SimpleMovingAverage(50)
        # Schedule Rollover Check
        self.schedule.on(
            self.date_rules.every_day(),
            self.time_rules.before_market_close(self.es_symbol, minutes_before_close=30),
            self.RollCheck
        )
        self.set_warm_up(timedelta(days=5))
        self.qty = 1
        self.rollover_liquidated = False
        self.contracts_available = None
    def FutureFilter(self, universe: FutureFilterUniverse):
        # Filter for contracts expiring within 90 days
        
        return universe.expiration_cycle([3,6,9,12])


    def on_data(self, slice: Slice):

        if self.is_warming_up:
            self.log("### Warming Up...")
            return
            # slice.future_chains
        chain = slice.future_chains.get(self.es_symbol)
        if not chain: return
        
        # Get current front contract by earliest expiry
        contracts = sorted([c for c in chain], key=lambda x: x.expiry)
        self.contracts_available = contracts
        if not contracts: return
        
        if self.active_contract is None:
            self.RollCheck()

        bar = slice.bars[self.active_contract]
        self._sma.update(bar.end_time, bar.close)

        if bar.close >= self._sma.current.value and not self.portfolio.invested:
            # Go Long
            if self.rollover_liquidated:
                self.market_order(self.active_contract, quantity=self.qty, tag="Rollover Long")
                self.rollover_liquidated = False
            else:
                self.market_order(self.active_contract, quantity=self.qty, tag="Long")
        elif bar.close <= self._sma.current.value and not self.portfolio.invested:
            # Go Short
            if self.rollover_liquidated:
                self.market_order(self.active_contract, quantity=-self.qty, tag="Rollover Short")
                self.rollover_liquidated = False
            else:
                self.market_order(self.active_contract, quantity=-self.qty, tag="Short")
        



    def RollCheck(self):
        # Roll if within 5 days to expiry
        contracts = self.contracts_available

        if not contracts:
            return
        # self.debug(f"contracts: {contracts}")
        closest_expiring_contract = min(contracts, key=lambda x: x.id.date)
        self.log(f"closest_expiring_contract: {closest_expiring_contract} at time: {self.time}")
        next_contract = sorted(contracts, key=lambda x: x.id.date)[1]
        self.log(f"next_contract: {next_contract} at time: {self.time}")
        if self.active_contract is not None and self.time >= self.next_rollover_date and self.portfolio.invested:
            self.liquidate(self.active_contract, tag="Rollover Liquidate")
            self.log(f"ROLLOVER EVENT: from {self.active_contract} to {next_contract}, date: {self.time}, current expiry: {self.active_contract.expiry}")
            self.rollover_liquidated = True
            self.active_contract = next_contract
            self.next_rollover_date = next_contract.expiry - timedelta(days=5)
        elif self.active_contract is None:
            self.active_contract = closest_expiring_contract
            self.next_rollover_date = closest_expiring_contract.expiry - timedelta(days=5)
        
        