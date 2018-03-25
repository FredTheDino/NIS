from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from time import sleep 
from math import floor

from seceret import *
from stocks import *
from log import *

import re

# Globals
valid_digit = re.compile("\d+,\d+")
valid_time = re.compile("\d+:\d+:\d+")
site = "https://www.avanza.se/"
closed = False
writen = False

driver = None

def get_stock_state(stock):
    login()
    goto_buy_page(stock)
    transaction_in_progress = is_selling_or_buying()
    

def login():
    # This doesn't load, IDK why... Sleeping fixes it
    if is_logged_in():
        return

    sleep(1.0)
    driver.find_element_by_css_selector("button.logInLink").click()
    if auto_login:
        # Fill in the form
        login_options = driver.find_elements_by_css_selector("a.toggleBar")
        # Click BankID to make sure everything else is closed.
        login_options[0].click()
        # Open the username stuff
        login_options[1].click()

        username_box = driver.find_element_by_css_selector("input[name='j_username']")
        username_box.clear()
        username_box.send_keys(username)

        password_box = driver.find_element_by_css_selector("input[name='j_password']")
        password_box.clear()
        password_box.send_keys(password)

        sleep(0.1)
        driver.find_element_by_css_selector("button.loginButton").click()
        sleep(0.1)
    else:
        input("Press enter once you are logged in to procedee")

def is_logged_in():
    # If the register button exists, we're logged in
    try:
        return driver.find_element_by_css_selector("a.register") == None
    except:
        return True

def is_selling_or_buying():
    elems = driver.find_elements_by_css_selector("div.component.current_orders div.content table tbody tr td.push-orderType")
    names = driver.find_elements_by_css_selector("div.component.current_orders div.content table tbody tr td.push-instrumentName a.link")

    index = -1
    for i in range(len(names)):
        # I know, don't judge
        if names[i].text.lower() in driver.title.lower():
            index = i
            break
    
    if index == -1:
        return ""
    if "Sälj" in elems[i].text:
        return "sell"
    elif "Köp" in elems[i].text:
        return "buy"
    else:
        return ""

def is_selling():
    return "sell" in is_selling_or_buying()

def is_buying():
    return "buy" in is_selling_or_buying()

class Trade(object):
    time_left = 0
    quantity = 0
    price = 0
    stock = None

    def __init__(self, stock, hour, minute, quantity, price):
        close_at_h = 17
        close_at_m = 30
        self.time_left = (close_at_h - hour) * 60 - minute + close_at_m
        self.quantity = quantity
        self.price = price
        self.stock = stock
        

def get_trade_info_prices(target):
    # Navigate to the site
    goto_trade_history_page(target)
    if not is_logged_in():
        login()
        goto_trade_history_page(target)

    ammounts = driver.find_elements_by_css_selector("td.tLeft + td.tLeft + td")
    prices = driver.find_elements_by_css_selector("td.tLeft + td.tLeft + td + td")
    times = driver.find_elements_by_css_selector("td + td.last")
    out = []
    for i in range(len(ammounts) - 1, -1, -1):
        print(prices[i].text)
        price    = float(prices[i].text.replace(",", "."))
        hour     = int(times[i].text.split(":")[0])
        minute   = int(times[i].text.split(":")[1])
        quantity = int("".join(ammounts[i].text.strip().split()))
        out.append(Trade(target, hour, minute, quantity, price))

    return out

def trade_history_page(stock):
    return site + "/aktier/dagens-avslut.html" + stock.stock

def goto_trade_history_page(stock):
    driver.get(trade_history_page(stock))

def buy_page(stock):
    return site + "/handla/aktier.html/kop" + stock.stock

def goto_buy_page(stock):
    driver.get(buy_page(stock))

def place_order(target, count, price, buying = True):
    # Navigate to the site
    driver.get(buy_page(target))
    sleep(0.5)
    while not is_logged_in():
        login()
        driver.get(buy_page(target))

    clear_orders(target)

    count_box = driver.find_element_by_css_selector("input#volume")
    count_box.clear()
    count_box.send_keys(str(count))

    price_box = driver.find_element_by_css_selector("input#price")
    price_box.clear()
    price_box.send_keys(str(round_to_nearest(price, target.smalest)))

    if buying:
        button = driver.find_element_by_css_selector("button.putorder.buy.buyBtn")
        button.click()
        sleep(0.5)
        try:
            driver.find_element_by_css_selector("button.focusBtn").click()
        except:
            pass
    else:
        button = driver.find_element_by_css_selector("button.putorder.sell.sellBtn")
        button.click()
        try:
            sleep(0.5)
            driver.find_element_by_css_selector("button.focusBtn").click()
            sleep(0.5)
            driver.find_element_by_css_selector("button.focusBtn").click()
        except:
            pass
    
    return True

def clear_orders(target):
    elems = driver.find_elements_by_css_selector("a.deleteOrder")
    names = driver.find_elements_by_css_selector("div.component.current_orders div.content table tbody tr td.push-instrumentName a.link")

    for i in range(len(names)):
        # I know, don't judge
        if names[i].text.lower() in driver.title.lower():
            elems[i].click()

def round_to_nearest(value, rounding_factor):
    return round(value * rounding_factor) / rounding_factor

def loop(target):
    global closed

    # Open the log file
    f = open("log.txt", "a")

    # Get out the sales info
    elems = get_trade_info_prices(target)
    current = elems[0]

    average = sum(elems) / len(elems);

    num_bottoms = 0
    sum_bottom = 0

    num_tops = 0
    sum_top = 0

    for p in elems:
        if p < average:
            sum_bottom = sum_bottom + p
            num_bottoms = num_bottoms + 1
        elif p > average:
            sum_top = sum_top + p
            num_tops = num_tops + 1
    

    lerp_top = 0.5
    top = (sum_top / num_tops) * lerp_top + (1 - lerp_top) * average

    lerp_bottom = 0.75
    bottom = (sum_bottom / num_bottoms) * lerp_bottom + (1 - lerp_bottom) * average

    # Round them to 4 decimal places
    top     = round_to_nearest(top,     1000)
    bottom  = round_to_nearest(bottom,  1000)

    # We need to check if we have any orders places
    driver.get(buy_page(target))

    status = driver.find_element_by_css_selector(".tradingPhase.SText.bold").text
    if "Stängd" in status:
        # Sorry, they're closed
        closed = True
        return
    closed = False

    diff = False
    if not target.last_top == top:
        target.last_top = top
        diff = True

    if not target.last_bottom == bottom:
        target.last_bottom = bottom
        diff = True

    if diff:
        log("({}) b: {}, t: {}, c: {}", target.stock, bottom, top, current)

    # What range we're happy with buying the stocks for
    if (
            current <= bottom and 
            not target.invested and 
            is_selling_or_buying() == ""
        ):
        # We want to buy and we don't own stock, and we're not selling
        count = floor(target.max_investment / current)
        
        if count != 0:
            # We have enough funds for buying
            target.invested = True
            target.count = 0
            target.buy_price = current
            target.loss_price = bottom * max_loss
            target.greed_price = top

            if place_order(target, count, current, True):
                target.count = count
                log("Ordered {} \nVol: {}, Price: {}, Exp: {}".format(
                        target.stock, count, current, (top - current) * count))
                # We are done with this loop.
                return
        else:
            log("Insufficent funds ({}) cost: {}, allowence: {}".format(
                    target.stock, current, target.max_investment))

    if is_selling_or_buying() == "" and target.invested:
        if place_order(target, target.count, target.greed_price, False):
            target.invested = False
            log("Selling ({}) For: {}, Profit: {}".format(
                    target.stock, current, 
                    (current - target.buy_price) * target.count))

            # This is needed for calculations
            target.count = 0
        
    if (current < target.loss_price
            and is_selling_or_buying() == "" and target.invested):
        if place_order(target, target.count, current, False):
            target.invested = False
            log("Selling with loss ({}) For: {}, Profit: {}".format(
                    target.stock, current, (current - target.buy_price) * target.count))

            # This is needed for calculations
            target.count = 0

    f.flush()
    f.close()

def init():
    global driver
    log("Started driver")

    profile = FirefoxProfile()

    if quick_mode:
        # Disable CSS
        # profile.set_preference('permissions.default.stylesheet', 2)
        # Disable images
        profile.set_preference('permissions.default.image', 2)
        # Disable Flash
        profile.set_preference('dom.ipc.plugins.enabled.libflashplayer.so',
                'false')
    driver = webdriver.Firefox(profile)

def main():
    global driver, writen, closed

    while True:
        try:
            init()
            while True:
                for target in stocks:
                    loop(target)
                    if closed:
                        break
                    writen = False
                
                if closed:
                    # 15 minutes of sleep if it's closed
                    if not writen:
                        log("Stock is closed, reloading in {} seconds."
                                .format(closed_refresh_time))
                        writen = True
                    # Sleepy time
                    sleep(closed_refresh_time)
                else:
                    # We wait a while, no need to refresh like every second.
                    sleep(reload_time)
        except Exception as e:
            print(e)
            # Something went wrong
            retry_time = 60
            log("Crashed, retrying in {} seconds.".format(retry_time))

            sleep(60)
            log("Trying again")
            driver.close()

if __name__ == "__main__":
    main()
