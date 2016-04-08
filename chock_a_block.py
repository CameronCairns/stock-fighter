import pdb

from utilities.utilities import AccountDaemon

if __name__ == '__main__':
    print('Level 2 Chock-a-Block')
    # Read level data from file
    attributes = ['api_key', 'account', 'venue', 'stock']
    information = dict(zip(attributes,
                           open('information.txt').read().splitlines()))
    #initialize account
    account = AccountDaemon(information['api_key'], information['account'])
    #initialize stock daemons
    venue = information['venue']
    account.spawn_stock_daemons(venue)
    #level involves just one stock so give it an easy to access name
    stock = account.stock_daemons[venue][information['stock']]
    average_price = int(input('Average Price:'))
    remaining_stock = 100000
    while(remaining_stock > 0):
        # Check Market Demand
        quote = stock.get_stock_quote()
        if(int(quote.get('askDepth', 0)) > 0 and
           int(quote.get('ask', average_price)) < average_price):
            # Sellers exist for desired stock and price is cheaper than average
            # so buy it
            quantity =(remaining_stock
                       if int(quote['askDepth']) > remaining_stock
                       else int(quote['askDepth']))
            order = stock.post_order(quantity,
                                     'immediate-or-cancel',
                                     price=int(quote['ask']))
            remaining_stock -= sum(fill['qty'] for fill in order['fills'])
