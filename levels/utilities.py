import requests

class APIDaemon:

    def __init__(self, *args, **kwargs):
        # Gather necessary apiKey and trading account for instantiating object
        apiKey = kwargs.pop('apiKey')
        account = kwargs.pop('account', 'EXB123456')
        # Test that input is in valid format
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

    def __init__(self, *args, **kwargs):
        super(StockDaemon, self).__init__(*args, **kwargs)
        self.venue = kwargs.pop('venue')
        self.stock = kwargs.pop('stock')
        self.orders = {}

    def __str__(self):
        return "{0}: {1}".format(self.venue, self.stock)

    def cancel_order(self, order):
        assert(isinstance(order, int))
        return self._post_to_api(
                "https://api.stockfighter.io/ob/api/venues/{0}/stocks/{1}/orders/{2}/cancel".format(self.venue, self.stock, order)
                )

    def get_order_status(self, order_id=None):
        if order_id:
            # User has defined a specific order to check the status for
            assert(isinstance(order_id, int))
            data = self._get_from_api(
                    "https://api.stockfighter.io/ob/api/venues/{0}/stocks/{1}/orders/{2}".format(self.venue, self.stock, order_id)
                    )
            return data if data.pop('ok') else data.pop('error', 'No error Specified')
        else:
            # No order id specified so return all orders for this stock on this venue
            data = self._get_from_api(
                    "https://api.stockfighter.io/ob/api/venues/{0}/accounts/{1}/orders".format(self.venue, self.account)
                    ).json()
            return data if data.pop('ok') else data.pop('error', 'No error Specified')


    def get_orderbook(self):
        data = self._get_from_api(
                "https://api.stockfighter.io/ob/api/venues/{0}/stocks/{1}".format(self.venue, self.stock)
                ).json()
        return({'bids': data['bids'], 'asks': data['asks']} if data['ok'] 
                 else data.pop('error', 'No error Specified'))

    def get_stock_quote(self):
        data = self._get_from_api(
                "https://api.stockfighter.io/ob/api/venues/{0}/stocks/{1}/quote".format(self.venue, self.stock)
                ).json()
        return data if data.pop('ok') else data.pop('error', 'No error Specified')

    def post_order(self,
                   price=0,
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
        data = self._post_to_api(
                "https://api.stockfighter.io/ob/api/venues/{0}/stocks/{1}/orders".format(self.venue, self.stock),
                {'account': self.account,
                 'venue': self.venue,
                 'stock': self.stock,
                 'price': price,
                 'qty': quantity,
                 'direction': direction,
                 'orderType': orderType,
                 }).json()
        return data if data.pop('ok') else data.pop('error', 'No error Specified')

class AccountDaemon(APIDaemon):

    def __init__(self, *args, **kwargs):
        super(AccountDaemon, self).__init__(*args, **kwargs)
        self.stock_daemons = {}

    def _api_up(self):
       return self._get_from_api("https://api.stockfighter.io/ob/api/heartbeat")

    def _get_venue_stocks(self, venue):
        return [ stock['symbol'] for stock in self._get_from_api(
                "https://api.stockfighter.io/ob/api/venues/{0}/stocks".format(venue)
                ).json()['symbols'] ]

    def _venue_up(self, venue):
        return self._get_from_api(
                "https://api.stockfighter.io/ob/api/venues/{0}/stocks".format(venue)
                )

    def get_all_order_status(self, venue=None):
        if venue:
            data = self._get_from_api(
                        "https://api.stockfighter.io/ob/api/venues/{0}/accounts/{1}/orders".format(venue, self.account)
                        ).json()
            return data if data.pop('ok') else data.pop('error', 'No error Specified')
        else:
            venue_statuses = {}
            for venue_name in self.stock_daemons.keys():
                data = self._get_from_api(
                            "https://api.stockfighter.io/ob/api/venues/{0}/accounts/{1}/orders".format(venue_name, self.account)
                            ).json()
                venue_statuses[venue_name] = data['orders'] if data.pop('ok') else data.pop('error', 'No error Specified')
            return venue_statuses

    def spawn_stock_daemons(self, venue='TESTEX'):
        assert(isinstance(venue, str))
        if(not self._api_up() or not self._venue_up(venue)):
            # Check that the API and Venue site status is up
            return None
        # initialize a new dictionary to hold all the stockdaemons
        self.stock_daemons[venue] = {}
        for stock in self._get_venue_stocks(venue):
            # Create a stockdaemon for every valid stock in venue
            assert(isinstance(stock, str))
            self.stock_daemons[venue][stock] = StockDaemon(
                                                    apiKey=self.apiKey,
                                                    account=self.account,
                                                    venue=venue,
                                                    stock=stock,
                                                    )
