import requests

class APIDaemon:
    """
    Handles all API calls for StockDaemon and AccountDaemon instances
    """
    # Make the session object a class variable to be used by all inheritors of
    # APIDaemon since each unique account, and api_key pair should use the same
    # persistent connection to speed up API requests
    __session = requests.Session()

    def __init__(self, api_key, account):
        self.api_key = api_key
        self.account = account


    def get_from_api(self, uri, params={}):
        return self.__session.get(
                "https://api.stockfighter.io/ob/api/" + uri,
                headers={'X-Starfighter-Authorization': self.api_key,},
                params={**params, **{'account': self.account}},
                )

    def post_to_api(self, uri, json={}):
        return self.__session.post(
                "https://api.stockfighter.io/ob/api/" + uri,
                headers={'X-Starfighter-Authorization': self.api_key,},
                json={**json, **{'account': self.account}},
                )

    _get_from_api = get_from_api
    _post_to_api = post_to_api

class StockDaemon(APIDaemon): 

    def __init__(self, api_key, account, venue, stock):
        super(StockDaemon, self).__init__(api_key, account)
        self.venue = venue
        self.stock = stock
        self.orders = {}

    def __str__(self):
        return "{0}: {1}".format(self.venue, self.stock)

    def cancel_order(self, order):
        uri = "venues/{0}/stocks/{1}/orders/{2}/cancel".format(self.venue,
                                                               self.stock,
                                                               order)
        return self._post_to_api(uri).json()

    def get_order_status(self, order_id=None):
        if order_id:
            # User has defined a specific order to check the status for
            uri = "venues/{0}/stocks/{1}/orders/{2}".format(self.venue, 
                                                            self.stock,
                                                            order_id)
            data = self._get_from_api(uri).json()
                
            return(data
                   if data.pop('ok')
                   else data.pop('error', 'No error Specified'))
        else:
            # No order id specified so return all orders for this stock on this
            # venue
            uri = "venues/{0}/accounts/{1}/orders".format(self.venue,
                                                          self.account)
            data = self._get_from_api(uri).json()
            return(data
                   if data.pop('ok')
                   else data.pop('error', 'No error Specified'))


    def get_orderbook(self):
        uri = "venues/{0}/stocks/{1}".format(self.venue, self.stock)
        data = self._get_from_api(uri).json()
        return({'bids': data.get('bids'), 'asks': data.get('asks')}
               if data.get('ok') 
               else data.pop('error', 'No error Specified'))

    def get_stock_quote(self):
        uri = "venues/{0}/stocks/{1}/quote".format(self.venue, self.stock)
        data = self._get_from_api(uri).json()
        return(data
               if data.pop('ok')
               else data.pop('error', 'No error Specified'))

    def post_order(self, quantity, orderType, price=0, direction='buy'):
        uri = "venues/{0}/stocks/{1}/orders".format(self.venue, self.stock)
        order = {'account': self.account,
                'venue': self.venue,
                'stock': self.stock,
                'price': price,
                'qty': quantity,
                'direction': direction,
                'orderType': orderType}
        data = self._post_to_api(uri, order).json()
                 
        return(data
               if data.pop('ok')
               else data.pop('error', 'No error Specified'))

class AccountDaemon(APIDaemon):

    # Methods for internal use, implementation may change
    def api_up(self):
       return self._get_from_api("heartbeat").ok

    def get_stocks(self, venue):
        uri = "venues/{0}/stocks".format(venue)
        return [stock['symbol']
                for stock
                in self._get_from_api(uri).json()['symbols']]

    def venue_up(self, venue):
        uri = "venues/{0}/stocks".format(venue)
        return self._get_from_api(uri).ok

    _api_up = api_up
    _get_stocks = get_stocks
    _venue_up = venue_up

    # Methods intended to be publicly callable
    def __init__(self, api_key, account):
        self.account = account
        self.api_key = api_key
        self.stock_daemons = None

    def get_all_order_statuses(self, venue=None):
        if venue:
            # Venue was specified so only return orders for that venue
            uri = "venues/{0}/accounts/{1}/orders".format(venue, self.account)
            data = self._get_from_api(uri).json()
            return(data['orders']
                   if data.pop('ok')
                   else data.pop('error', 'No error Specified'))
        else:
            # No venue specified so instead get all orders for all active
            # venues
            venues = self.stock_daemons.keys()
            venue_data = [self._get_from_api(
                            "venues/{0}/accounts/{1}/orders".format(
                                venue, self.account)).json()
                          for venue
                          in venues]
            venues_order_statuses = {venue: venue_data[pos]['orders']
                                     if venue_data[pos].pop('ok')
                                     else venue_data[pos].pop(
                                         'error', 'No error Specified')
                                     for pos, venue
                                     in enumerate(venues)}
            return venues_order_statuses

    def spawn_stock_daemons(self, *venues):
        # Generate all active venues to allow for stock daemon creation
        # for all stocks on each active venue
        active_venues = (venue
                         for venue
                         in venues
                         if self._venue_up(venue))
        # Create dictionary to hold all the stockdaemons associated with
        # each active venue
        self.stock_daemons = {venue: {stock: StockDaemon(self.api_key,
                                                         self.account,
                                                         venue,
                                                         stock)
                                      for stock
                                      in self._get_stocks(venue)}
                              for venue
                              in active_venues}

if __name__ == '__main__':
    # Test suite for Stockfighter API interface
    api_key = input('Enter API Key')
    account = AccountDaemon(api_key=api_key, account='EXB123456')
    account.spawn_stock_daemons('TESTEX')
    order_statuses = account.get_all_order_statuses()
    for venue in account.stock_daemons:
        order_statuses = account.get_all_order_statuses(venue)
        for stock in account.stock_daemons[venue]:
            stock_daemon = account.stock_daemons[venue][stock]
            orderbook = stock_daemon.get_orderbook()
            quote = stock_daemon.get_stock_quote()
            order = stock_daemon.post_order(1000, 'limit')
            order_status = stock_daemon.get_order_status(order['id'])
            cancelled = stock_daemon.cancel_order(order['id'])
            order_status = stock_daemon.get_order_status(order['id'])
