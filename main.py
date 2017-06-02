#!/usr/bin/python
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from time import sleep 
from math import floor
from seceret import *
import re
import datetime

# Globals
valid_input = re.compile("\d+,\d+")
site = "https://www.avanza.se/"
closed = False

def print_time_stamp():
    now = datetime.datetime.now()
    print("[{0:0>2}:{1:0>2}]".format(now.hour, now.minute))

def login():
    # This doesn't load, IDK why... Sleeping fixes it
    sleep(0.5)
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
        input("Press enter once you are logged in")

def is_logged_in():
    # Is is the register button, if it doesn't exist, we're logged in
    try:
        return driver.find_element_by_css_selector("a.register") == None
    except:
        return True

def is_selling_or_buying():
    elem = driver.find_element_by_css_selector("div.component.current_orders div.content table tbody tr td.push-orderType")
    if "Sälj" in elem.text:
        return "sell"
    elif "Köp" in elem.text:
        return "buy"
    return ""

def is_selling():
    return "sell" in is_selling_or_buying()

def is_buying():
    return "buy" in is_selling_or_buying()

def trade_history_page(stock):
    return site + "/aktier/dagens-avslut.html" + stock.stock

def get_trade_info_prices(target):
    # Navigate to the site
    driver.get(trade_history_page(target))
    if not is_logged_in():
        login()
        driver.get(trade_history_page(target))

    elem = driver.find_elements_by_css_selector("td.tLeft + td.tLeft + td + td")
    out = []
    for e in elem:
        if valid_input.search(e.text):
            out.append(float(e.text.replace(",", ".")))

    return out

def buy_page(stock):
    return site + "/handla/aktier.html/kop" + stock.stock

def place_order(target, count, price, buying = True):
    # Navigate to the site
    driver.get(buy_page(target))
    if not is_logged_in():
        login()
        driver.get(buy_page(target))

    count_box = driver.find_element_by_css_selector("input#volume")
    count_box.clear()
    count_box.send_keys(str(count))

    price_box = driver.find_element_by_css_selector("input#price")
    price_box.clear()
    price_box.send_keys(str(price))

    if buying:
        button = driver.find_element_by_css_selector("button.putorder.buy.buyBtn")
        button.click()
        sleep(0.1)
        driver.find_element_by_css_selector("button.focusBtn").click()
    else:
        button = driver.find_element_by_css_selector("button.putorder.sell.sellBtn")
        button.click()
        sleep(0.1)
        driver.find_element_by_css_selector("button.focusBtn").click()
        sleep(0.1)
        driver.find_element_by_css_selector("button.focusBtn").click()
    
    return True

greed = 0.1 # How much the stock should increase before selling
max_loss = 0.2 # How much we are willing to sell for at its cheapest

def loop(target):
    global closed
    # Get out the sales info
    elems = get_trade_info_prices(target)
    current = elems[0]
    bottom = min(elems)
    top = max(elems)



    # We need to check if we have any orders places
    driver.get(buy_page(target))

    status = driver.find_element_by_css_selector(".tradingPhase.SText.bold").text
    if "Stängd" in status:
        # Sorry, they're closed
        closed = True
        return False
    closed = False

    # What range we're happy with buying the stocks for
    delta = 0.01
    if (
            abs(current - bottom) <= delta and 
            not target.invested and 
            is_selling_or_buying() == ""
        ):
        # We want to buy and we don't own stock, and we're not selling
        sell_price = current + greed
        count = floor(target.max_investment / sell_price)
        
        if count != 0:
            # We have enough funds for buying
            target.invested = True
            target.owned_amount = 0
            target.buy_price = current
            target.greed_price = sell_price
            target.loss_price = current - max_loss

            if place_order(target, count, current, True):
                print_time_stamp()
                print("Placed order on ", target.stock, "\nVolume: ", count, ", For: ", current, ", Expected Profit: ", greed * count)
        else:
            print_time_stamp()
            print("Insufficent funds for transaction ({})".format(target.stock))
        
    delta = 0.01
    if ((current + delta <= target.loss_price or current >= target.greed_price)
            and is_selling_or_buying() == "" and target.invested):
        if place_order(target, target.owned_amount, current, False):
            target.owned_amount = 0
            target.invested = False
            print_time_stamp()
            print("Selling ", target.stock, "\nExpected Profit: ", (target.buy_price - current) * target.count, " For: ", current)


driver = None
writen = False
def main():
    global driver, writen, closed

    try:
        driver = webdriver.Firefox()
        while True:
            for target in stocks:
                loop(target)
                if closed:
                    break
                writen = False

            if closed:
                # 15 minutes of sleep if it's closed
                if not writen:
                    print_time_stamp()
                    print("Open soon?")
                    writen = True
                # Sleepy time
                sleep(60 * 15)
    except:
        # Something went wrong
        sleep(60)
        print_time_stamp()
        print("Trying again")
        driver.close()

if __name__ == "__main__":
    main()
