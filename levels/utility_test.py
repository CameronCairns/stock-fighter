import pdb

from utilities import AccountDaemon

pdb.set_trace()

test_account = AccountDaemon(apiKey='a842566b1b9e4a53fd5a29cff3729ec4790b7823')

test_account.spawn_stock_daemons()

for stock_daemon in test_account.stock_daemons['TESTEX'].values():
    stock_daemon.get_orderbook() 
    stock_daemon.get_stock_quote() 
    order = stock_daemon.post_order() 
    stock_daemon.get_order_status() 
    stock_daemon.cancel_order(order['id']) 

test_account.get_all_order_status()
