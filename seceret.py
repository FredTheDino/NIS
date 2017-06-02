class Target:
    stock = ""
    invested = False
    max_investment = 1
    # Invalid value to say we don't have one
    buy_price = -1
    greed_price = -1
    loss_price = -1
    owned_amount = 0

    def __init__(self, stock, max_investment):
        self.stock = stock
        self.max_investment = max_investment

# You might not be able to use auto login,
# since you need to fill in a code in the 
# mail for that to work.
# 
# This tries to log in with the credentials
# bellow. If you set this to False, you
# will do the loggin in.
auto_login = False

# Leave empty if un used, for your own protection
username = ""
password = ""

# A list of stocks to trade with,
# it expects the last part of the URL, which tells
# the server which stock it is we're looing at.
#
# The second part is the max spending for a purchas.
# The computer will buy as many as it can for this 
# price every time. 
stocks = [Target("/5480/anoto-group", 1)]
#        Target("/755803/munters-group", 1),
#        Target("/757512/terranet-holding-b", 1)]

