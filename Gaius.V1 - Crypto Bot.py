from urllib.parse import urlencode
import urllib.request
import json
import time
import sys
import hmac
import hashlib
from datetime import datetime
from dateutil import tz

print('Started at:', datetime.utcnow())

class bittrex(object):
    
    def __init__(self, key, secret):
        self.key = key
        self.secret = secret
        self.public = ['getmarkets', 'getcurrencies', 'getticker', 'getmarketsummaries', 'getmarketsummary', 'getorderbook', 'getmarkethistory']
        self.market = ['buylimit', 'buymarket', 'selllimit', 'sellmarket', 'cancel', 'getopenorders']
        self.account = ['getbalances', 'getbalance', 'getdepositaddress', 'withdraw', 'getorder', 'getorderhistory', 'getwithdrawalhistory', 'getdeposithistory']
    
    
    def query(self, method, values={}):
        if method in self.public:
            url = 'https://bittrex.com/api/v1.1/public/'
        elif method in self.market:
            url = 'https://bittrex.com/api/v1.1/market/'
        elif method in self.account: 
            url = 'https://bittrex.com/api/v1.1/account/'
        else:
            return 'Something went wrong, sorry.'
        
        url += method + '?' + urlencode(values)
        
        if method not in self.public:
            url += '&apikey=' + self.key
            url += '&nonce=' + str(int(time.time()))
            signature = hmac.new(str.encode(self.secret), str.encode(url), hashlib.sha512).hexdigest()
            headers = {'apisign': signature}
        else:
            headers = {}
        
        req = urllib.request.Request(url, headers=headers)
        response = json.loads(urllib.request.urlopen(req).read())

        if response["result"]:
            return response["result"]
        else:
            return response["message"]
    
    
    def getmarkets(self):
        return self.query('getmarkets')
    
    def getcurrencies(self):
        return self.query('getcurrencies')
    
    def getticker(self, market):
        return self.query('getticker', {'market': market})
    
    def getmarketsummaries(self):
        return self.query('getmarketsummaries')
    
    def getmarketsummary(self, market):
        return self.query('getmarketsummary', {'market': market})
    
    def getorderbook(self, market, type, depth=20):
        return self.query('getorderbook', {'market': market, 'type': type, 'depth': depth})
    
    def getmarkethistory(self, market, count=20):
        return self.query('getmarkethistory', {'market': market, 'count': count})
    
    def buylimit(self, market, quantity, rate):
        return self.query('buylimit', {'market': market, 'quantity': quantity, 'rate': rate})
    
    def buymarket(self, market, quantity):
        return self.query('buymarket', {'market': market, 'quantity': quantity})
    
    def selllimit(self, market, quantity, rate):
        return self.query('selllimit', {'market': market, 'quantity': quantity, 'rate': rate})
    
    def sellmarket(self, market, quantity):
        return self.query('sellmarket', {'market': market, 'quantity': quantity})
    
    def cancel(self, uuid):
        return self.query('cancel', {'uuid': uuid})
    
    def getopenorders(self, market):
        return self.query('getopenorders', {'market': market})
    
    def getbalances(self):
        return self.query('getbalances')
    
    def getbalance(self, currency):
        return self.query('getbalance', {'currency': currency})
    
    def getdepositaddress(self, currency):
        return self.query('getdepositaddress', {'currency': currency})
    
    def withdraw(self, currency, quantity, address):
        return self.query('withdraw', {'currency': currency, 'quantity': quantity, 'address': address})
    
    def getorder(self, uuid):
        return self.query('getorder', {'uuid': uuid})
    
    def getorderhistory(self, market, count):
        return self.query('getorderhistory', {'market': market, 'count': count})
    
    def getwithdrawalhistory(self, currency, count):
        return self.query('getwithdrawalhistory', {'currency': currency, 'count': count})
    
    def getdeposithistory(self, currency, count):
        return self.query('getdeposithistory', {'currency': currency, 'count': count})

bot = bittrex('', '')


#Get current market orders/history 
#Get volume? 
#What's important is how much is being traded and how fast the price is shifting. 
#For instance, if a fast bump is detected but low volume, the market will fix itself and go low again. 
#If a large volume is detected, there's conviction and it's 'safer' to assume this will be a more permanent change in the market. 


#Gaius the Scalper 
#WATCH, AQUIRE, DISPOSE 
phase = None
ticker = "USDT-BTC"

class Gaius():
	global phase 
	def __init__(self):
		self.big_buyer_limit = 100
		self.market = "USDT"
		self.currency = "BTC"
		self.sell_at_loss = '1.06'
		self.sell_at_buy = '0.95'
		self.old_orders = []
		self.action = 0
		self.last_order = None
		self.sell_gain = None
		self.sell_loss = None
		self.order_id = None

	def Run(self):
		#buying
		if self.action == 0:
			if not self.old_orders:
				data = bot.getmarkethistory(self.market + '-' + self.currency)
				for order in data:
					self.old_orders.append(order)
			else:
				data = bot.getmarkethistory(self.market + '-' + self.currency)
				for order in data:
					if order['Quantity'] > 10:
						for banned_order in self.old_orders:
							if order['Id'] == banned_order['Id']:
								break
						self.action = 1
						self.old_orders[:] = []
						#buy max
						Buy_Max_Amount(self.market, self.currency)

		elif self.action == 1:
			#get rate at which you bought
			#sell or buy depending on where it goes and your deficiet 
			if self.last_order == None:
				data = bot.getorderhistory('USDT-BTC', 0)
				if data[0]['OrderType'] == 'LIMIT_SELL':
					print('last order was a sell')
					self.last_order = data[0]['Limit']
					print('The buy price was at', self.last_order)
					self.sell_gain = self.last_order * 1.06
					self.sell_loss = self.last_order * 0.95
			else:
				a = bot.getticker('USDT-BTC')
				wallet = bot.getbalance('BTC')
				print('current rate:', a['result']['Last'] * wallet['Available'], 'desired high/low:', self.sell_gain,'/',self.sell_loss)
				if a['result']['Last'] * wallet['Available'] > self.sell_gain:
					num = a['Ask'] * wallet['Available']
					num = round(num * .9975, 8)
					z = bot.selllimit('USDT-BTC', num, self.sell_gain)
					if z['result'] == True:
						while True:
							data = bot.getopenorders('USDT-BTC')
							if data['success'] == True and len(data['result'][0]) > 0:
								print('waiting for order to fill')
							elif data['success'] == True and len(data['result'][0]) == 0:
								print('order completely filled')
								self.action = 2
								break
							else:
								print('something went wrong in buy max amount, exiting')
								sys.exit(1)

				elif a['result']['Last'] * wallet['Available'] < self.sell_loss:
					num = a['Ask'] * wallet['Available']
					num = round(num * .9975, 8)
					z = bot.selllimit('USDT-BTC', num, self.sell_loss)
					if z['result'] == True:
						while True:
							data = bot.getopenorders('USDT-BTC')
							if data['success'] == True and len(data['result'][0]) > 0:
								print('waiting for order to fill')
							elif data['success'] == True and len(data['result'][0]) == 0:
								print('order completely filled')
								self.action = 2
								break
							else:
								print('something went wrong in buy max amount, exiting')
								sys.exit(1)
		elif self.action == 2:
			print('bot finished one iteration, ending program')
			sys.exit(1)


def Buy_Max_Amount():
	asking_price = bot.getticker('USDT-BTC')
	wallet = bot.getbalance('USDT')
	print(asking_price)
	print(wallet)
	# a = asking_price['Ask'] * wallet['Available']
	# a = round(a * .9975, 8) if im selling idc about the ask 
	a = wallet['Available'] / asking_price['Ask'] 
	a = round(a * .9975, 8)
	v = bot.buylimit('USDT-BTC', a, asking_price['Ask'])
	if v == 'DUST_TRADE_DISALLOWED_MIN_VALUE_50K_SAT':
		print('maximum amount purchased')
		return 
	elif v['success'] == False: 
		print('failed to place buy order, exiting')
		sys.exit(1)
	else:
		while True:
			data = bot.getopenorders('USDT-BTC')
			if data['success'] == True and len(data['result'][0]) > 0:
				print('waiting for order to fill')
			elif data['success'] == True and len(data['result'][0]) == 0:
				print('order completely filled')
				break
			else:
				print('something went wrong in buy max amount, exiting')
				sys.exit(1)

			time.sleep(2)


# a = bot.getorderhistory('BTC-LTC', 9)
# print(a)

THE_ONE = Gaius()

# a = bot.selllimit('BTC-LTC', '0.31141335', '0.00937901')
# print(a)

while True:
	THE_ONE.Run()
	time.sleep(1)


