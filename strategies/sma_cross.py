import backtrader as bt


class TeamStrategy(bt.Strategy):
    params = dict(
        fast=10,
        slow=30,
        stake=1,
        printlog=False,
    )

    def __init__(self):
        sma_fast = bt.ind.SMA(self.datas[0].close, period=self.p.fast)
        sma_slow = bt.ind.SMA(self.datas[0].close, period=self.p.slow)
        self.crossover = bt.ind.CrossOver(sma_fast, sma_slow)

    def next(self):
        if not self.position:
            if self.crossover > 0:
                self.buy(size=self.p.stake)
        else:
            if self.crossover < 0:
                self.sell(size=self.p.stake)

    def log(self, txt, dt=None):
        if self.p.printlog:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()} {txt}')

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status in [order.Completed]:
            self.log(f'ORDER {order.getordername()} EXECUTED, price={order.executed.price} size={order.executed.size}')
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')
