'''
Created on Jan 21, 2016

@author: Wei
'''
import os, csv, requests
from datetime import datetime, timedelta
import time, random
import lxml.etree as ET
# import lxml
from io import StringIO


# import urllib.request
datapath = 'c:/stock/data/daily/'
dataHeader = ['Expiration', 'Type', 'Contract Name', 'Last Trade Date', 'Strike', 'Last Price', 'Bid', 'Ask', 'Change', 
              '% Change', 'Volume', 'Open Interest', 'Implied Volatility']


class OptionData():
    header = {'User-Agent':'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.16 Safari/537.36'}

    @staticmethod
    def get_option_data(symbol):
        "e.g, https://finance.yahoo.com/quote/AAPL/options?p=AAPL"
        
        s1 = "https://finance.yahoo.com/quote/"
        s2 = "/options?p="
        url0 = s1 + symbol + s2 + symbol
        
        response = requests.get(url0, headers=OptionData.header)

        parser = ET.HTMLParser(remove_comments=True)
        root = ET.parse(StringIO(response.text), parser)
#         print(ET.tostring(root))
#         root = ET.fromstring(StringIO(response.text))
        
        dates = root.xpath("//select")[0]
        dateInfo = [(d.get('value'), d.text) for d in dates]
        
        expDays = [(code, datetime.strptime(exp, '%B %d, %Y').strftime('%Y-%m-%d')) for code, exp in dateInfo]
        
        data = OptionData.get_option_data_single_day(root, expDays[0][1])
        if len(data)==0:
            return 2
        
        for code, expDay in expDays[1:]:
            url = url0 + '&date=' + code
            response = requests.get(url, headers=OptionData.header)
            root = ET.parse(StringIO(response.text), parser)
            
            dataday = OptionData.get_option_data_single_day(root, expDay)
            data += dataday
        
        today = Utility.get_business_date()
        fname = 'option' + today.strftime("%Y-%m-%d") + '.csv'
        
        foldername = datapath + symbol + '/'
        filename = foldername + fname 
        with open(filename, 'w', newline='') as f:
            wr = csv.writer(f, dialect='excel')
            for row in data:
                wr.writerow(row)
    
        return 1
        
    @staticmethod
    def get_option_data_single_day(root, expDay):
        dates = root.xpath("//select")[0]
        dateInfo = [(d.get('value'), d.text) for d in dates]
        
        data = []
        tables = root.xpath("//table")
        for table in tables:
            tableClass = table.get('class')
            if tableClass.startswith('calls'):
                optType = 'call'
            elif tableClass.startswith('puts'):
                optType = 'put'
            else:
                continue
            
#             theadElems = table.xpath('./thead/tr')
#             thead = theadElems[0]

#             cols = thead.xpath('./th/span') 
#             s = ', '.join([c.text for c in cols])
#             print(s)
            
            tbodyElems = table.xpath('./tbody')
            tbody = tbodyElems[0]
            for tr in tbody:
                row = [expDay, optType]
                for td in tr:
                    c = td.text
                    if not c:
                        c = td.findtext('a')
                        if not c:
                            c=td.findtext('span')
                            
                    row.append(c)
                
                data.append(row)
#                 print(', '.join(row))
 
        return data
        
class NetFondData:
    @staticmethod
    def get_intraday_data(symbol):
        
        url='http://hopey.netfonds.no/tradedump.php?date=20171128&paper=AAPL.O&csv_format=csv';
        response = requests.get(url)
        
# #         try:
# #             response = requests.get(url)
# #         except Exception as e:
# #             return str(e)
#             
        content = response.content.decode('utf-8')
         
        foldername = datapath + symbol
        if not os.path.exists(foldername):
            os.makedirs(foldername)
        cr = csv.reader(content.splitlines(), delimiter=',')
#         records = [row for row in cr]
        records = list(cr)

        filename = 'test.csv'
        with open(filename, 'wb') as f:
            f.write(response.content)
        
        return 1
    
class AlphaVantageData():
    apiKey = '2MS04W5F3UPTT84H'
    
    @staticmethod
    def get_intraday_data(symbol):
        ##: e.g., https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=MSFT&interval=1min&outputsize=full&apikey=2MS04W5F3UPTT84H&datatype=csv
        s1 = 'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol='
        s2 = '&interval=1min&outputsize=full&apikey=2MS04W5F3UPTT84H&datatype=csv'
        url = s1 + symbol + s2
        response = requests.get(url)
        
#         try:
#             response = requests.get(url)
#         except Exception as e:
#             return str(e)
            
        content = response.content.decode('utf-8')
        
        foldername = datapath + symbol
        if not os.path.exists(foldername):
            os.makedirs(foldername)
        cr = csv.reader(content.splitlines(), delimiter=',')
#         records = [row for row in cr]
        records = list(cr)
        if len(records)==0:
            return 2 
        
        time_end = records[1][0]
        time_begin = records[-1][0]
        str_begin = time_begin[:10] + '.' + time_begin[11:13] + '.' +time_begin[14:16]
        str_end = time_end[:10] + '.' + time_end[11:13] + '.' + time_end[14:16]
        fname = str_begin + '_' + str_end + '.csv'
#         today = datetime.today()
        filename = foldername + '/' + fname
        with open(filename, 'wb') as f:
            f.write(response.content)
        
        return 1
"""
It seems that you are already a user. As a reminder, your API key is: 2MS04W5F3UPTT84H. 
Please record this API key for lifetime access to Alpha Vantage.
"""
class Utility:
    @staticmethod
    def get_business_date():
        today = datetime.today()
        now = datetime.now()
        hr = now.hour
        if hr < 9:
            d = 1
        elif hr==9 and now.minute<30:
            d = 1
        else:
            d = 0
        
        bday = datetime.today() - timedelta(days=d)
            
        return bday
    
    @staticmethod
    def create_symbol_list_all():
        filenameNASDAQ = './companylist_NASDAQ.csv'
        filenameNYSE = './companylist_NYSE.csv'
#         filename = './companylist_AMEX.csv'
        
        threshold_marketcap = 400000000
        
        ##: Open data file
        try:
            with open(filenameNASDAQ, 'r') as f:
                reader = csv.reader(f)
                raw_data1 = [row for row in reader]
                for row in raw_data1:
                    row[2] = row[1]
                    row[1] = 'NASDAQ'
                    
##:         Symbol   Exchange  Name   MarketCap    IPOyear    Sector    industry    Summary Quote

            with open(filenameNYSE, 'r') as f:
                reader = csv.reader(f)
                raw_data2 = [row for row in reader]
                for row in raw_data2:
                    row[2] = row[1]
                    row[1] = 'NYSE'
                
        except Exception as e:
            print(str(e))
            return
        
        data = []
        raw_data = raw_data1[1:] + raw_data2[1:]
        for row in raw_data:
            cap = row[3]
            if cap[0]!='$': continue
            if cap[-1]=='M':
                val = float(cap[1:-1])*1000000
            elif cap[-1]=='B':
                val = float(cap[1:-1])*1000000000
            else: ##: $12732.9
#                 print(row[1] + ": data is wrong!")
                continue
            
            if val<threshold_marketcap:
                continue
            row[3] = str(val) 
            
            row[-1].strip()
            
            data.append(row)
        
        writer = csv.writer(open("./company_full_list.csv", 'w', newline=''))
#         writer.writerows(data)
        for row in data:
            writer.writerow(row)
        
        return data

        
class DataCollector:
        
    @staticmethod
    def collect_intraday_data(startid=0):
        DataCollector.collect_data_all_companies(AlphaVantageData.get_intraday_data, startid)
        
    @staticmethod
    def collect_option_data(startid=0):
        DataCollector.collect_data_all_companies(OptionData.get_option_data, startid)
        
    @staticmethod
    def collect_data_all_companies(func_for_symbol, startid=0):
                
        with open("./company_full_list.csv", newline='') as csvfile:
            reader = csv.reader(csvfile)
            companies = [row for row in reader]
        
        today = datetime.today()
        logfilename = './log/log_' + today.strftime('%Y-%m-%d') + '.log'
        
#         startid = 0
        symbols = [c[0] for c in companies]
        unsuccessful = []
        for i, symbol in enumerate(symbols):
            if i < startid:
                continue
            
            flag = -1
            try:
                flag = func_for_symbol(symbol)
                msg = str(flag)
            except Exception as e:
                msg = str(e)
            
            if flag!=1:
                unsuccessful.append((i, symbol))
                
            with open(logfilename, "a") as logfile:
                s = str(i) + ', ' + symbol + ', ' + msg + '\n'
                logfile.write(s)
                print(s)
            
            time.sleep(1+random.random())  ##: wait for 1~2 sec to fake browser visit
        
        ##: Retry on unsuccessful symbols
        with open(logfilename, "a") as logfile:
            s = '\n**********Retry on unsuccessful symbols**********\n'
            logfile.write(s)
            print(s)
        
        bad_symbols = []
        for i, symbol in unsuccessful:
            flag = -1
            try:
                flag = func_for_symbol(symbol)
                msg = str(flag)
            except Exception as e:
                msg = str(e)
            
            if flag!=1:
                bad_symbols.append((i, symbol))
            
            with open(logfilename, "a") as logfile:
                s = str(i) + ', ' + symbol + ', ' + msg + '\n'
                logfile.write(s)
                print(s)
            
            time.sleep(1+random.random())  ##: wait for 1~2 sec to fake browser visit
        
        with open(logfilename, "a") as logfile:
            s = '\n**********Bad symbols**********\n'
            logfile.write(s)
            print(s)
            for i, symbol in bad_symbols:
                s = str(i)+', ' + symbol
                logfile.write(s + '\n')
                print(s)
                
    @staticmethod
    def collect_intraday_data_old():
                
        with open("./company_full_list.csv", newline='') as csvfile:
            reader = csv.reader(csvfile)
            companies = [row for row in reader]
        
        today = datetime.today()
        logfilename = 'log_' + today.strftime('%Y-%m-%d') + '.log'
        
        symbols = [c[0] for c in companies]
        unsuccessful = []
        for i, symbol in enumerate(symbols):
            flag = -1
            try:
                flag = AlphaVantageData.get_intraday_data(symbol)
                msg = str(flag)
            except Exception as e:
                msg = str(e)
            
            if flag!=1:
                unsuccessful.append((i, symbol))
                
            with open(logfilename, "a") as logfile:
                s = str(i) + ', ' + symbol + ', ' + msg + '\n'
                logfile.write(s)
                print(s)
            
            time.sleep(1+random.random())  ##: wait for 1~2 sec to fake browser visit
        
        ##: Retry on unsuccessful symbols
        with open(logfilename, "a") as logfile:
            s = '\n**********Retry on unsuccessful symbols**********\n'
            logfile.write(s)
            print(s)
        
        bad_symbols = []
        for i, symbol in unsuccessful:
            flag = -1
            try:
                flag = AlphaVantageData.get_intraday_data(symbol)
                msg = str(flag)
            except Exception as e:
                msg = str(e)
            
            if flag!=1:
                bad_symbols.append((i, symbol))
            
            with open(logfilename, "a") as logfile:
                s = str(i) + ', ' + symbol + ', ' + msg + '\n'
                logfile.write(s)
                print(s)
            
            time.sleep(1+random.random())  ##: wait for 1~2 sec to fake browser visit
        
        with open(logfilename, "a") as logfile:
            s = '\n**********Bad symbols**********\n'
            logfile.write(s)
            print(s)
            for i, symbol in bad_symbols:
                s = str(i)+', ' + symbol
                logfile.write(s)
                print(s)
        
if __name__ == '__main__':
#     OptionData.get_option_data('AAPL')
#     Utility.create_symbol_list_all()
#     AlphaVantageData.get_intraday_data('MSFT')
#     NetFondData.get_intraday_data('')

    DataCollector.collect_intraday_data()
#     DataCollector.collect_option_data(1787)
    
    print('Program Finished!!!')        
    