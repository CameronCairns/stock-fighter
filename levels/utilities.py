import requests

class APIDaemon:

    def __init__(self, apiKey, account='EXB123456'):
        assert(all((isinstance(apiKey, str), isinstance(account, str))))
        self.account = account
        self.apiKey = apiKey

    def _get_from_api(self, url):
        return requests.get(
                url,
                headers={'X-Starfighter-Authorization': self.apiKey,})

    def _post_to_api(self, url, json={}):
        return requests.post(
                url,
                headers={'X-Starfighter-Authorization': self.apiKey,},
                json=json)

class StockDaemon(APIDaemon): 

    def __init__(self, venue, stock, *args, **kwargs):
        assert(all((isinstance(venue, str), isinstance(stock, str))))
        super(StockDaemon, self).__init__(*args, **kwargs)
        self.venue = venue
        self.stock = stock
        URLS = {
            'stock_orderbook': "https://api.stockfighter.io/ob/api/venues/{0}/stocks/{1}".format(venue, stock),
            'stock_quote': "https://api.stockfighter.io/ob/api/venues/{0}/stocks/{1}/quote".format(venue, stock),
            }

    def get_orderbook(self):
        data = requests.get(self.apiUrls[request]).json()
        return data if data.pop('ok') else data.pop('error', 'No error Specified')

    def post_order(price=0,
                   quantity=100,
                   direction='buy',
                   orderType='market'):
        assert(all((
                    isinstance(price, int),
                    isinstance(quantity, int),
                    isinstance(direction, str),
                    isinstance(orderType, str),
                    )
                   )
               )
        response= _post_to_api(
                "https://api.stockfighter.io/ob/api/venues/{0}/stocks/{1}/orders".format(venue, stock),
                {'account': self.account,
                 'venue': self.venue,
                 'stock': self.stock,
                 'price': price,
                 'qty': quantity,
                 'direction': direction,
                 'orderType': orderType,
                 })
        return filter(lambda x: x.pop(['ok']), response.json())

    def delete_order(self, order):
        assert(isinstance(order, int))
        return _post_to_api(
                "https://api.stockfighter.io/ob/api/venues/{0}/stocks/{1}/orders/{2}/cancel".format(self.venue, self.stock, order)
                )

    def get_order_status(self, order):
        assert(isinstance(order, int))
        return _get_from_api(
                "https://api.stockfighter.io/ob/api/venues/{0}/stocks/{1}/orders/{2}".format(self.venue, self.stock, order)
                )

    def get_all_order_status(self):
        assert(isinstance(order, int))
        response = _get_from_api(
                "https://api.stockfighter.io/ob/api/venues/{0}/stocks/{1}/orders".format(self.venue, self.stock)
                ).json()

    def get_stock_quote(venue='TESTEX', stock='FOOBAR'):
        assert(all((isinstance(venue, str), isinstance(stock, str))))
        response = requests.get(url)
        return filter(lambda x: bool(x.pop(['ok'])), response.json())

class AccountDaemon(APIDaemon):

    def __init__(self, *args, **kwargs):
        super(AccountDaemon, self).__init__(*args, **kwargs)
        self.stockdaemons = {}

    def _api_up(self):
       return self._get_from_api("https://api.stockfighter.io/ob/api/heartbeat")

    def _get_venue_stocks(self,venue):
        return [ stock for stock['symbol'] in self._get_from_api(
                "https://api.stockfighter.io/ob/api/venues/{0}/stocks".format(venue)
                ).json()['symbols'] ]

    def _get_venue_orders(self, venue):
        return self._get_from_api(
                "https://api.stockfighter.io/ob/api/venues/{0}/accounts/{1}/orders".format(venue, account)
                ).json()

    def _venue_up(self, venue):
        return self._get_from_api(
                "https://api.stockfighter.io/ob/api/venues/{0}/stocks".format(venue),
                )

    def spawn_daemons(self, venue='TESTEX'):
        if(not self._api_up() or not self._venue_up(venue)):
            # Check that the API and Venue site status is up
            return None
        # initialize a new dictionary to hold all the stockdaemons
        self.stockdaemons[venue] = {}
        for stock in self._get_venue_stocks(venue):
            # Create a stockdaemon for every valid stock in venue
            self.stockdaemons[venue][stock] = StockDaemon(
                                                    apiKey=self.apiKey,
                                                    account=self.account,
                                                    venue=venue,
                                                    stock=stock,
                                                    )

    def check_all_orders_for_venue(venue):
        return [ order for order in self._get_venue_orders(venue) ]
