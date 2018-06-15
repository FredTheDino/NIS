#!/usr/bin/python3
# coding=utf-8
from log import log
import driver_interface as d
from stocks import stocks as STOCKS
from time import sleep 

class stock_state(object):
    # Logik data
    value = 0 # Värde som vi tänker köpa för.
    on_value = False # Om vi är på "value" eller inte.
    peeked = 0 # Hur många gånger vi gått över värdet.
    value_needs_update = True # Om vi ska updatera "value" snarast möjligt.
    set_at = 0 # När vi senast satte "value"
    time_left = 24 * 60 # Hur lång tid i minuter tills börsen stänger.
    stock = None
    
    placed_order = False # Om vi har placerat en order.
    holding = False # Om vi äger aktier.
    holding_quantity = 0
    last_active_order = ""

    buy_price = 0 # Vad vi köpte aktien för.
    sell_price = 0 # Vad vi vill sälja för.

    # Stats
    profit = 0 # Hur mycket vinnst vi fått.
    trades = 0 # Antal trades
    good_trades = 0 # Hur många trades vi gjort vinst på

    bought_for = 0 # Hur mycket vi har köpt för.
    sold_for = 0 # Hur mycker vi har sålt för.
    max_buy = 0 # Dyraste vi köpt.

    def __init__(self, stock):
        self.stock = stock

    # Vi går ett tidssteg framåt.
    def update(self, trade, active_order):
        # Makesure we're not counting trades double.
        if (trade.time_left < 0):
            return "Done for today"
        if (self.time_left < trade.time_left):
            return "- Allready done"

        # We successfully baught or sold
        if (self.placed_order 
                and self.last_active_order != active_order):
            if self.last_active_order == "sell":
                self.value_needs_update = False
                self.holding = False

                self.trades = self.trades + 1
                self.profit = self.profit + (self.sell_price - self.buy_price)
                self.sold_for = self.sold_for + self.sell_price

            elif self.last_active_order == "buy":
                if self.max_buy < self.buy_price:
                    self.max_buy = self.buy_price
                self.bought_for = self.bought_for + price
                self.holding = True

        log(active_order)
        self.last_active_order = active_order
        self.time_left = trade.time_left
        price = trade.price
        if "sell" in active_order and self.placed_order:
            # Hantera ordern så att vi inte DÖR
            return self.handle_sell(price)
        elif "buy" in active_order and self.placed_order:
            # Hantera ordern så att vi inte DÖR
            return self.handle_buy(price)
        elif self.holding:
            # Om vi äger något, försök att sälja.
            return self.try_sell(price)
        elif 60 < self.time_left:
            # Försök köpa om vi inte har ont om tid.
            return self.try_buy(price)
        # Dom stänger snart så ingen mening med att göra något.
        return "DONE"

    # Beräknar det pris vi vill sälja för.
    def get_sell_price(self):
        # Hur mycket är vi villiga att sälja för.
        if self.time_left < 60:
            # Vi är desperata.
            return self.buy_price + 0.01
        else:
            return self.buy_price + 0.02

    # Om allt går åt skogen, sälj för detta.
    # Värde för att förhindra pris ras. 
    def get_min_sell_price(self):
        return self.buy_price - 0.05

    # Se 
    def get_min_value(self):
        return self.value - 0.05

    def get_max_value(self):
        return self.value + 0.05

    # Vi säljer
    def sell(self, price):
        if (d.place_order(self.stock, self.quantity, price, False)):
            self.sell_price = price
            self.placed_order = True

    # Vi kollar om vi kan sälja.
    def try_sell(self, price):
        # Se till så börsen inte stänger på oss.
        # (Borde nog göra detta till en funktion.)
        if self.get_sell_price(self.time_left) <= price:
            # Updatera statestiken
            self.good_trades = self.good_trades + 1
            self.sell(self.get_sell_price(self.time_left))
            # Logga ut vad som hände.
            return "Sell for profit"
        # Logga ut vad som hände, nämligen inget.
        return ""

    def handle_sell(self, price):
        if price <= self.get_min_sell_price(self.time_left):
            # Vi säljer för att vi måste.
            self.sell(price - 0.01) # Detta kan vara lite kontroversiellt
            # Logga ut vad som hände.
            return "Sell for loss"
        return "Waiting"

    # Vi köper.
    def buy(self, price):
        # Beräkna hur många vi vill köpa, vi vill alltid köpa så många som möjligt.
        quantity = int(self.stock.max_investment / price)
        if (d.place_order(self.stock, quantity, price, True)):
            # Vad vi köpte för.
            self.buy_price = price
            self.placed_order = True
            self.quantity = quantity
    
    # Vi sätter vårt refferensvärde.
    def set_value(self, price):
        # Återställer vårt state.
        self.value_needs_update = False
        self.on_value = True
        self.peeked = 0
        self.value = price
        self.set_at = self.time_left

        return "Set value to {}".format(price)

    def handle_buy(slef, price):
        if price <= self.get_min_value():
            self.value = price
            self.peeked = 0
            d.clear_orders(self.stock)
            return self.set_value(price)

    # Vi kollar om vi kan köpa.
    def try_buy(self, price):
        # Om vi inte har ett värde, set det.
        if self.value_needs_update:
            return self.set_value(price)

        # Om det var länge sedan vi satte värdet, updatera det.
        if 10 < self.set_at - self.time_left:
            self.set_value(price)
            return "Timedout, set value to {}".format(price)
        
        # En flagga som kollar om vi är tillbaka på värdet.
        back_on_value = False
        if not self.on_value and price == self.value:
            # Om vi inte var på värdet tidagre och är det nu,
            # så vet vi det nu.
            back_on_value = True
            self.on_value = True

        # Om vi är över vårt utgångs värde, och vi var på
        # vårt värde förra updateringen.
        if self.value < price and self.on_value:
            # Då har vi nått en "peek", alltså att
            # värdet går upp över.
            self.on_value = False
            self.peeked = self.peeked + 1
            return "Peeked ({})".format(self.peeked)

        # Om vi har peekat 2 gånger, då köper vi.
        elif price == self.value and 2 <= self.peeked :
            self.buy(price)
            return "Bought"

        # Om värdet är under utgångs värdet, då
        # kollar vi om vi måste sälja.
        elif price <= self.get_min_value() or price >= self.get_max_value():
            self.value = price
            self.peeked = 0
            return self.set_value(price)

        elif back_on_value:
            # Om vi bytte tillbaka till värdet,
            # och inget annat hände, då loggar vi
            # det. Någon kanske bryr sig.
            return "Back to value ({})".format(price)

        return ""

def main():
    d.init()
    states = []
    for stock in STOCKS:
        states.append(stock_state(stock))

    while True:
        for state in states:
            trans = d.get_stock_state(state.stock)
            trades = d.get_trade_info_prices(state.stock)
            log(trans)
            for trade in trades:
                if trans == None:
                    trans = ""
                

                #trans = d.is_selling_or_buying()
                action = state.update(trade, trans)
                if action != "":
                    if action[0] != "-":
                        log(action)


        sleep(10)

if __name__ == "__main__":
    main()

