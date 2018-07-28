# Gist example of IB wrapper ...
#
# Download API from http://interactivebrokers.github.io/#
#
# Install python API code /IBJts/source/pythonclient $ python3 setup.py install
#
# Note: The basicApp cases, and the documentation refer to a python package called IBApi,
#    but the actual package is called ibapi. Go figure.
#
# Get the latest version of the gateway:
# https://www.interactivebrokers.com/en/?f=%2Fen%2Fcontrol%2Fsystemstandalone-ibGateway.php%3Fos%3Dunix
#    (for unix: windows and mac users please find your own version)
#
# Run the gateway
#
# user: edemo
# pwd: demo123
#
# Now I'll try and replicate the historical data example

from ibapi.wrapper import EWrapper
from ibapi.client import EClient
# from ibapi.contract import Contract as IBcontract
from ibapi.contract import Contract
from ibapi.ticktype import TickTypeEnum

import pandas as pd
import numpy as np

import time
from threading import Thread
import queue
import datetime


DEFAULT_MARKET_DATA_ID=50
DEFAULT_GET_CONTRACT_ID=43

## marker for when queue is finished
FINISHED = object()
STARTED = object()
TIME_OUT = object()

class finishableQueue(object):

    def __init__(self, queue_to_finish):

        self._queue = queue_to_finish
        self.status = STARTED

    def get(self, timeout):
        """
        Returns a list of queue elements once timeout is finished, or a FINISHED flag is received in the queue
        :param timeout: how long to wait before giving up
        :return: list of queue elements
        """
        contents_of_queue=[]
        finished=False

        while not finished:
            try:
                current_element = self._queue.get(timeout=timeout)
                if current_element is FINISHED:
                    finished = True
                    self.status = FINISHED
                else:
                    contents_of_queue.append(current_element)
                    ## keep going and try and get more data

            except queue.Empty:
                ## If we hit a time out it's most probable we're not getting a finished element any time soon
                ## give up and return what we have
                finished = True
                self.status = TIME_OUT


        return contents_of_queue

    def timed_out(self):
        return self.status is TIME_OUT


def _nan_or_int(x):
    try:
        n = int(x)
        return n
    except:
        return None
#     
#     if not x:
#         return int(x)
#     else:
#         return x

class stream_of_ticks(list):
    """
    Stream of ticks
    """
 
    def __init__(self, list_of_ticks):
        super().__init__(list_of_ticks)
 
    def as_pdDataFrame(self):
 
        if len(self)==0:
            ## no data; do a blank tick
            return tick(datetime.datetime.now()).as_pandas_row()
 
        pd_row_list=[tick.as_pandas_row() for tick in self]
        pd_data_frame=pd.concat(pd_row_list)
 
        return pd_data_frame


class tick(object):
    """
    Convenience method for storing ticks
    Not IB specific, use as abstract
    """
    def __init__(self, timestamp, bid_size=None, bid_price=None,
                 ask_size=None, ask_price=None,
                 last_trade_size=None, last_trade_price=None,
                 ignorable_tick_id=None):

        ## ignorable_tick_id keyword must match what is used in the IBtick class

        self.timestamp=timestamp
        self.bid_size=_nan_or_int(bid_size)
        self.bid_price=bid_price
        self.ask_size=_nan_or_int(ask_size)
        self.ask_price=ask_price
        self.last_trade_size=_nan_or_int(last_trade_size)
        self.last_trade_price=last_trade_price

    def __repr__(self):
        return self.as_pandas_row().__repr__()

    def as_pandas_row(self):
        """
        Tick as a pandas dataframe, single row, so we can concat together
        :return: pd.DataFrame
        """

        attributes=['bid_size','bid_price', 'ask_size', 'ask_price',
                    'last_trade_size', 'last_trade_price']

#         self_as_dict=dict([(attr_name, getattr(self, attr_name)) for attr_name in attributes])
#         return pd.DataFrame(self_as_dict, index=[self.timestamp])
    
        return [(attr_name, getattr(self, attr_name)) for attr_name in attributes]

class IBtick(tick):
    """
    Resolve IB tick categories
    """

    def __init__(self, timestamp, tickid, value):

        resolve_tickid=self.resolve_tickids(tickid)
        super().__init__(timestamp, **dict([(resolve_tickid, value)]))

    def resolve_tickids(self, tickid):
        ##: Find reference at https://interactivebrokers.github.io/tws-api/tick_types.html#gsc.tab=0
        tickid_dict=dict([("0", "bid_size"), ("1", "bid_price"), ("2", "ask_price"), ("3", "ask_size"),
                          ("4", "last_trade_price"), ("5", "last_trade_size")])

        if str(tickid) in tickid_dict.keys():
            return tickid_dict[str(tickid)]
        else:
            # This must be the same as the argument name in the parent class
            return "ignorable_tick_id"



class MyWrapper(EWrapper):
    """
    The wrapper deals with the action coming back from the IB gateway or TWS instance
    We override methods in EWrapper that will get called when this action happens, like currentTime
    Extra methods are added as we need to store the results in this object
    """

    def __init__(self):
        self._my_contract_details = {}
        self._my_market_data_dict = {}
        self._my_realtime_bar_dict = {}
        self._my_option_data_dict = {}
        self._my_market_depth_dict = {}

    ## error handling code
    def init_error(self):
        error_queue=queue.Queue()
        self._my_errors = error_queue

    def get_error(self, timeout=5):
        if self.is_error():
            try:
                return self._my_errors.get(timeout=timeout)
            except queue.Empty:
                return None

        return None

    def is_error(self):
        an_error_if=not self._my_errors.empty()
        return an_error_if

    def error(self, id, errorCode, errorString):
        ## Overriden method
        errormsg = "IB error id %d errorcode %d string %s" % (id, errorCode, errorString)
        self._my_errors.put(errormsg)


    ## get contract details code
    def init_contractdetails(self, reqId):
        contract_details_queue = self._my_contract_details[reqId] = queue.Queue()

        return contract_details_queue

    def contractDetails(self, reqId, contractDetails):
        ## overridden method

        if reqId not in self._my_contract_details.keys():
            self.init_contractdetails(reqId)

        self._my_contract_details[reqId].put(contractDetails)

    def contractDetailsEnd(self, reqId):
        ## overriden method
        if reqId not in self._my_contract_details.keys():
            self.init_contractdetails(reqId)

        self._my_contract_details[reqId].put(FINISHED)

    # market data
    def init_market_data(self, tickerid):
        market_data_queue = self._my_market_data_dict[tickerid] = queue.Queue()

        return market_data_queue

    # market depth
    def init_market_depth_queue(self, tickerid):
        market_depth_queue = self._my_market_depth_dict[tickerid] = queue.Queue()

        return market_depth_queue


    # option
    def init_option_data_queue(self, tickerid):
        option_data_queue = self._my_option_data_dict[tickerid] = queue.Queue()

        return option_data_queue
    
    # market data
    def init_realtime_bar_queue(self, tickerid):
        realtime_bar_queue = self._my_realtime_bar_dict[tickerid] = queue.Queue()

        return realtime_bar_queue

    def get_time_stamp(self):
        ## Time stamp to apply to market data
        ## We could also use IB server time
        return datetime.datetime.now()

    def realtimeBar(self, reqId:int, time:int, open:float, high:float, low:float, close:float, volume:int, wap:float, count:int):
#     def realtimeBar(self, reqId, time, open, high, low, close, volume, wap, count):
        super().realtimeBar(reqId, time, open, high, low, close, volume, wap, count)
        print("RealTimeBars. ", reqId, ": time ", time, ", open: ",open, ", high: ", high, ", low: ", low, ", close: ", close, ", volume: ", volume, ", wap: ", wap, ", count: ", count)
    # ! [realtimebar]
# 



    def updateMktDepth(self, reqId: int, position: int, operation: int,
                       side: int, price: float, size: int):
        super().updateMktDepth(reqId, position, operation, side, price, size)
        print("UpdateMarketDepth. ", reqId, "Position:", position, "Operation:",
              operation, "Side:", side, "Price:", price, "Size", size)

    # ! [updatemktdepth]


    def updateMktDepthL2(self, reqId: int, position: int, marketMaker: str,
                         operation: int, side: int, price: float, size: int):
        super().updateMktDepthL2(reqId, position, marketMaker, operation, side,
                                 price, size)
        print("UpdateMarketDepthL2. ", reqId, "Position:", position, "Operation:",
              operation, "Side:", side, "Price:", price, "Size", size)

    # ! [updatemktdepthl2]

#         this_tick_data=IBtick(self.get_time_stamp(),tickType, price)
        self._my_market_depth_dict[reqId].put(this_tick_data)

        self._my_option_data_dict = {}
        self._my_market_depth_dict = {}


#     def tickPrice(self, tickerid , tickType, price, attrib):
#         ##overriden method
# 
#         ## For simplicity I'm ignoring these but they could be useful to you...
#         ## See the documentation http://interactivebrokers.github.io/tws-api/md_receive.html#gsc.tab=0
#         # attrib.canAutoExecute
#         # attrib.pastLimit
# 
#         this_tick_data=IBtick(self.get_time_stamp(),tickType, price)
#         self._my_market_data_dict[tickerid].put(this_tick_data)
# 
# 
#     def tickSize(self, reqId, tickType, size):
#         ## overriden method
# 
#         print("Tick Size. Ticker Id:", reqId, "Type:", TickTypeEnum.to_str(tickType), "Size:", size)
#         this_tick_data=IBtick(self.get_time_stamp(), tickType, size)
#         self._my_market_data_dict[reqId].put(this_tick_data)
# 
# 
#     def tickString(self, reqId, tickType, value):
#         ## overriden method
# 
# #     def tickString(self, reqId: TickerId, tickType: TickType, value: str):
# #         super().tickString(reqId, tickType, value)
#         print("Tick string. Ticker Id:", reqId, "Type:", tickType, "Value:", value)
#         
#         ## value is a string, make it a float, and then in the parent class will be resolved to int if size
#         if tickType>6:
#             return
#         this_tick_data=IBtick(self.get_time_stamp(),tickType, float(value))
#         self._my_market_data_dict[reqId].put(this_tick_data)
# 
# 
#     def tickGeneric(self, reqId, tickType, value):
#         ## overriden method
# 
#         print("Tick Generic. Ticker Id:", reqId, "Type:", TickTypeEnum.to_str(tickType), "Value:", value)
#         this_tick_data=IBtick(self.get_time_stamp(),tickType, value)
#         self._my_market_data_dict[reqId].put(this_tick_data)



class MyClient(EClient):
    """
    The client method
    We don't override native methods, but instead call them from our own wrappers
    """
    def __init__(self, wrapper):
        ## Set up with a wrapper inside
        EClient.__init__(self, wrapper)

        self._market_data_q_dict = {}
        self._realtime_bar_q_dict = {}
        self._market_depth_q_dict = {}
        self._option_data_q_dict = {}

    def resolve_ib_contract(self, ibcontract, reqId=DEFAULT_GET_CONTRACT_ID):

        """
        From a partially formed contract, returns a fully fledged version
        :returns fully resolved IB contract
        """

        ## Make a place to store the data we're going to return
        contract_details_queue = finishableQueue(self.init_contractdetails(reqId))

        print("Getting full contract details from the server... ")

        self.reqContractDetails(reqId, ibcontract)

        ## Run until we get a valid contract(s) or get bored waiting
        MAX_WAIT_SECONDS = 10
        new_contract_details = contract_details_queue.get(timeout = MAX_WAIT_SECONDS)

        while self.wrapper.is_error():
            print(self.get_error())

        if contract_details_queue.timed_out():
            print("Exceeded maximum wait for wrapper to confirm finished - seems to be normal behaviour")

        if len(new_contract_details)==0:
            print("Failed to get additional contract details: returning unresolved contract")
            return ibcontract

        if len(new_contract_details)>1:
            print("got multiple contracts using first one")

        new_contract_details=new_contract_details[0]

        resolved_ibcontract=new_contract_details.summary

        return resolved_ibcontract

    def start_getting_realtime_bar(self, contract, reqId):
        self._realtime_bar_q_dict[reqId] = self.wrapper.init_realtime_bar_queue(reqId)
        self.reqRealTimeBars(reqId, contract, 5, "TRADES", True, [])
    
        
    def start_getting_IB_market_data(self, resolved_ibcontract, tickerid=DEFAULT_MARKET_DATA_ID):
        """
        Kick off market data streaming
        :param resolved_ibcontract: a Contract object
        :param tickerid: the identifier for the request
        :return: tickerid
        """

        self._market_data_q_dict[tickerid] = self.wrapper.init_market_data(tickerid)
        self.reqMktData(tickerid, resolved_ibcontract, "", False, False, [])

        return tickerid


    def start_getting_mkt_depth_data(self, contract, reqId):
        self._market_depth_q_dict[reqId] = self.wrapper.init_market_depth_queue(reqId)
#     def marketDepthOperations_req(self):
        # Requesting the Deep Book
        # ! [reqmarketdepth]
#         self.reqMktDepth(reqId, contract, 5, [])
        
        contract = Contract()
        contract.symbol = "EUR"
        contract.secType = "CASH"
        contract.currency = "GBP"
        contract.exchange = "IDEALPRO"
        self.reqMktDepth(2001, contract, 5, [])
        
        # ! [reqmarketdepth]

        # Request list of exchanges sending market depth to UpdateMktDepthL2()
        # ! [reqMktDepthExchanges]
        self.reqMktDepthExchanges()
        # ! [reqMktDepthExchanges]

    def stop_getting_realtime_bar(self, reqId):
        """
        Stops the stream of market data and returns all the data we've had since we last asked for it
        :param tickerid: identifier for the request
        :return: market data
        """
        
        self.cancelRealTimeBars(reqId)

    def stop_getting_IB_market_depth(self, reqId):
        """
        Stops the stream of market data and returns all the data we've had since we last asked for it
        :param tickerid: identifier for the request
        :return: market data
        """
        
        self.cancelMktDepth(reqId)

    def stop_getting_IB_market_data(self, reqId):
        """
        Stops the stream of market data and returns all the data we've had since we last asked for it
        :param tickerid: identifier for the request
        :return: market data
        """

        ## native EClient method
        self.cancelMktData(reqId)

        self.cancelMktDepth(reqId)
#         ## Sometimes a lag whilst this happens, this prevents 'orphan' ticks appearing
#         time.sleep(5)
# 
#         market_data = self.get_IB_market_data(tickerid)
# 
#         ## output ay errors
#         while self.wrapper.is_error():
#             print(self.get_error())
# 
#         return market_data

    def get_IB_market_data(self, tickerid):
        """
        Takes all the market data we have received so far out of the stack, and clear the stack
        :param tickerid: identifier for the request
        :return: market data
        """

        ## how long to wait for next item
        MAX_WAIT_MARKETDATEITEM = 5
        market_data_q = self._market_data_q_dict[tickerid]

        market_data=[]
        finished=False

        while not finished:
            try:
                market_data.append(market_data_q.get(timeout=MAX_WAIT_MARKETDATEITEM))
            except queue.Empty:
                ## no more data
                finished=True

        return stream_of_ticks(market_data)


class MyApp(MyWrapper, MyClient):
    def __init__(self, ipaddress, portid, clientid):
        MyWrapper.__init__(self)
        MyClient.__init__(self, wrapper=self)

        self.connect(ipaddress, portid, clientid)
        self.contracts = self.create_contracts()

        thread = Thread(target = self.run)
        thread.start()

        setattr(self, "_thread", thread)

        self.init_error()
    
    def create_contracts(self):
        symbols = ['IBM', 'EDU']
        contracts = []
        for i, symbol in enumerate(symbols):
            contract = Contract();
            contract.symbol = symbol
            contract.secType = "STK";
            contract.exchange = "SMART";
            contract.currency = "USD";
            tickerid = i
            contracts.append((tickerid, contract))
        
        return contracts
    
    def start_everything(self):
        for reqId, contract in self.contracts:
#             self.start_getting_IB_market_data(contract, reqId)
            self.start_getting_realtime_bar(contract, reqId)
            self.start_getting_mkt_depth_data(contract, reqId)
        
        while not self.wrapper.is_error():
            time.sleep(5)
            self.export_data()
        else:
            print(self.get_error())
        
    def export_data(self):
        for tickerid, contract in self.contracts:
            market_data = self.get_IB_market_data(tickerid)
            print(market_data)

        ## output ay errors
        while self.wrapper.is_error():
            print(self.get_error())

        return market_data
    
    def stop_everying(self):
        for tickerid, contract in self.contracts:
#             self.stop_getting_IB_market_data(tickerid)
            self.stop_getting_realtime_bar(tickerid)
            self.stop_getting_IB_market_depth(tickerid)
    
    def req_mkt_data(self, symbol):
        contract = Contract();
        contract.symbol = "TSLA";
        contract.secType = "STK";
        contract.exchange = "SMART";
        contract.currency = "USD";
    
        self.reqMktData(1001, contract, "220", False, False, [])

def main():
    app = MyApp("127.0.0.1", 4001, 0)
    app.start_everything()
    
    time.sleep(60)

    app.stop_everying()

#     contract = Contract();
#     contract.symbol = "VIX";
#     contract.secType = "FUT";
#     contract.exchange = "CFE";
#     contract.currency = "USD";
#     contract.lastTradeDateOrContractMonth = "20170621";
    
#     symbols = ['IBM', 'EDU']
#     
#     contract = Contract();
#     contract.symbol = "TSLA";
#     contract.secType = "STK";
#     contract.exchange = "SMART";
#     contract.currency = "USD";
#     
#     app.reqMktData(1001, contract, "220", False, False, [])
#     
#     app.run()

if __name__ == '__main__':
    main()
    
#     
# #if __name__ == '__main__':
# 
# app = MyApp("127.0.0.1", 4001, 1)
# 
# ## lets get prices for this
# ibcontract = IBcontract()
# ibcontract.secType = "FUT"
# ibcontract.lastTradeDateOrContractMonth="201812"
# ibcontract.symbol="GE"
# ibcontract.exchange="GLOBEX"
# 
# ## resolve the contract
# resolved_ibcontract = app.resolve_ib_contract(ibcontract)
# 
# tickerid = app.start_getting_IB_market_data(resolved_ibcontract)
# 
# time.sleep(30)
# 
# ## What have we got so far?
# market_data1 = app.get_IB_market_data(tickerid)
# 
# print(market_data1[0])
# 
# market_data1_as_df = market_data1.as_pdDataFrame()
# print(market_data1_as_df)
# 
# time.sleep(30)
# 
# ## stops the stream and returns all the data we've got so far
# market_data2 = app.stop_getting_IB_market_data(tickerid)
# 
# ## glue the data together
# market_data2_as_df = market_data2.as_pdDataFrame()
# all_market_data_as_df = pd.concat([market_data1_as_df, market_data2_as_df])
# 
# ## show some quotes
# some_quotes = all_market_data_as_df.resample("1S").last()[["bid_size", "bid_price", "ask_price", "ask_size"]]
# print(some_quotes.head(10))
# 
# ## show some trades
# some_trades = all_market_data_as_df.resample("10L").last()[["last_trade_price", "last_trade_size"]]
# print(some_trades.head(10))
# 
# app.disconnect()
