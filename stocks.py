class Target:
    stock = ""
    invested = False
    max_investment = 1

    last_bottom = -1
    last_top = -1

    smalest = 1
    # Invalid value to say we don't have one
    buy_price = -1
    greed_price = -1
    loss_price = -1
    count = 0

    def __init__(self, stock, max_investment, smalest):
        self.stock = stock
        self.max_investment = max_investment
        self.smalest = smalest

# A list of stocks to trade with,
# it expects the last part of the URL, which tells
# the server which stock it is we're looing at.
#
# The second part is the max spending for a purchas.
# The computer will buy as many as it can for this 
# price every time. 
stocks = [Target("/637261/bull-omx-x15-ava-4", 1008,  1000)]
            
            

