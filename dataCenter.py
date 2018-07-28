'''
Created on Dec 24, 2017

@author: Wei.Wang
'''

import csv, os, sqlite3
import numpy as np
from datetime import datetime, timedelta
from dateutil.parser import parse
from matplotlib.dates import date2num

dataSources = ['IntradayGoogle', 'IntradayVantage', 'MarketDepthNetFonds', 'TickDataNetFonds', 'IntradayQuandl']
plotTypes = ['Line', 'Bar']
intervals = ['1 min', 'hourly', 'daily', '5 min','15 min','30 min', '5 hour', 'monthly', 'yearly']

class DataCenter:
    
    @staticmethod
    def get_data_files(symbol, startDatetime, endDatetime, dataSource):
        if dataSource in ['IntradayGoogle', 'MarketDepthNetFonds', 'TickDataNetFonds']:
            datafolder = 'C:/stock/code_Matlab/data/' + symbol + '/daily/'
        elif dataSource == 'IntradayVantage':
            datafolder = 'c:/stock/data/daily/' + symbol +'/'
        else:
            print('No data source!!!!!!!!!')
        
        prefix = ''
        if dataSource=='IntradayGoogle':
            prefix = 'G'
        elif dataSource=='MarketDepthNetFonds':
            prefix = 'NT'
        elif dataSource=='TickDataNetFonds':
            prefix = 'NP'
        else:
            print('No data source!!!!!!!!!')
        
        files = []
        fname = datafolder + prefix + startDatetime.strftime('%Y%m%d')+'_'+symbol+'.csv'
        if os.path.exists(fname):
            files.append(fname)
        numdays = (endDatetime - startDatetime).days
        for i in range(1, numdays+1):
            day = startDatetime + timedelta(days = i)
            fname = datafolder + prefix + day.strftime('%Y%m%d')+'_'+symbol+'.csv'
            if os.path.exists(fname):
                files.append(fname)
                    
        return files
        
    @staticmethod
    def get_intraday_data(symbol, startDatetime, endDatetime, dataSource, interval):
        """
        quotes : sequence of quote sequences
        data to plot.  time must be in float date format - see date2num
        (time, open, high, low, close, volume) 
        """
        
        datafiles = DataCenter.get_data_files(symbol, startDatetime, endDatetime, dataSource)
        
        data = []
        for datafile in datafiles:
            try:
                with open(datafile, 'r') as f:
                    reader = csv.reader(f)
                    raw_data = [row for row in reader]
            except Exception as e:
                print(str(e))
                return
            
            header = []
            ##: The second column are usually numbers if not a header
            try:
                float(raw_data[0][1])
            except:
                header = raw_data[0]
                raw_data = raw_data[1:]
            
#             data0 = [[date2num(parse(r[0]))] + [float(c) for c in r[1:5]] + [int(r[5])] for r in raw_data]
            data0 = [[parse(r[0])] + [float(c) for c in r[1:5]] + [int(r[5])] for r in raw_data]
            
            data += data0
        
        if interval!='1 min':
            data = DataCenter.aggregate_intraday_data(data, interval)
        
        return data

    @staticmethod
    def aggregate_intraday_data(quotes, intvl):
        """
        Input: quotes - sequence of quote sequences with minute interval (time, open, high, low, close, volume)
               interval - datetime.timedelta, or a string from ['1 min', 'hourly', 'daily', '5 min','15 min','30 min', '5 hour', 'monthly', 'yearly']
        """
        
        if isinstance(intvl, str):
            if 'min' in intvl:
                n = int(intvl[:-3])
                interval = timedelta(minutes = n)
            elif 'daily'==intvl:
                interval = timedelta(days = 1)
            elif 'hour' in intvl:
                if 'hourly' in intvl:
                    interval = timedelta(hours = 1)
                else:
                    interval = timedelta(hours = int(intvl[:-5]))
            elif 'monthly'==intvl:
                interval = timedelta(days=30)
            else:
                interval = intvl
        else:
            interval = intvl
        
        data = []
        ncol = len(quotes[0])-1
        segStart = quotes[0][0]
        if segStart.minute!=30 or segStart.second!=0:
            segStart = segStart.replace(hour=9, minute=30, second=0)
        block = []
        for rec in quotes:
            if rec[0] - segStart >= interval:
                if len(block)>0: 
                    open = block[0][1]
                    close = block[-1][4]
                    high = max([r[2] for r in block])
                    low = min([r[3] for r in block])
                    volume = sum([r[5] for r in block])
                    data.append([segStart, open, high, low, close, volume])
                block = []
                segStart = rec[0]
            block.append(rec)
        
        if len(block)>0:
            open = block[0][1]
            close = block[-1][4]
            high = max([r[2] for r in block])
            low = min([r[3] for r in block])
            volume = sum([r[5] for r in block])
            data.append([segStart, open, high, low, close, volume])

        return data

class Indicators():
    @staticmethod
    def MCSD(data):
        return
    
class Utility:
    @staticmethod
    def moving_average(x, n, type='simple'):
        """
        compute an n period moving average.

        type is 'simple' | 'exponential'

        """
        x = np.asarray(x)
        if type == 'simple':
            weights = np.ones(n)
        else:
            weights = np.exp(np.linspace(-1., 0., n))

        weights /= weights.sum()

        a = np.convolve(x, weights, mode='full')[:len(x)]
        a[:n] = a[n]
        return a

    @staticmethod
    def relative_strength(prices, n=14):
        """
        compute the n period relative strength indicator
        http://stockcharts.com/school/doku.php?id=chart_school:glossary_r#relativestrengthindex
        http://www.investopedia.com/terms/r/rsi.asp
        """

        deltas = np.diff(prices)
        seed = deltas[:n+1]
        up = seed[seed >= 0].sum()/n
        down = -seed[seed < 0].sum()/n
        rs = up/down
        rsi = np.zeros_like(prices)
        rsi[:n] = 100. - 100./(1. + rs)

        for i in range(n, len(prices)):
            delta = deltas[i - 1]  # cause the diff is 1 shorter

            if delta > 0:
                upval = delta
                downval = 0.
            else:
                upval = 0.
                downval = -delta

            up = (up*(n - 1) + upval)/n
            down = (down*(n - 1) + downval)/n

            rs = up/down
            rsi[i] = 100. - 100./(1. + rs)

        return rsi

    @staticmethod
    def moving_average_convergence(x, nslow=26, nfast=12):
        """
        compute the MACD (Moving Average Convergence/Divergence) using a fast and slow exponential moving avg'
        return value is emaslow, emafast, macd which are len(x) arrays
        """
        emaslow = Utility.moving_average(x, nslow, type='exponential')
        emafast = Utility.moving_average(x, nfast, type='exponential')
        
        return emaslow, emafast, emafast - emaslow

class DBStore:
    """This class handles database operations."""    
    def __init__(self, dbname):
        self.schema = ""
        
        if os.path.isfile('FEC.sqlite'):
            self.conn = sqlite3.connect(dbname)
            self.conn.text_factory = str
            self.c = self.conn.cursor()
        else:
            self.conn = sqlite3.connect(dbname)
            self.conn.text_factory = str
            self.c = self.conn.cursor()      
            self.create_tables()      

    def close(self):
        self.conn.close()
        
    def create_tables(self):
        """Create tables in the database"""
        self.c.execute("create table if not exists EMPLOYEES (EmployeeID text primary key,  FirstName text not null, LastName text not null,  \
              Address text, City text, State text, Zip text, PhoneNumber text, Email text, \
              Title text, Salary float, YearJoined text, Password text)")
    
        self.c.execute("create table if not exists TASKS (TaskID integer primary key, Name text, Role text)")
        
        self.c.execute("create table if not exists SCHEDULE (EmployeeID text, WeekStartDate text, SunAM text, SunPM text, MonAM text, MonPM text, \
             TueAM text, TuePM text, WedAM text, WedPM text, ThuAM text, ThuPM text, FriAM text, FriPM text, SatAM text, SatPM text)")
        
        self.c.execute("create table if not exists ATTENDANCE (Number integer, DateTime text)")
                
        self.import_data()
        
    def import_data(self):
        """Generate example database for testing and reviewing."""
        
        ##: Generate records for the Employees Table
        try:
            with open('employees.csv', 'r') as f:
                reader = csv.reader(f)
                raw_data = [row for row in reader]
        except Exception as e:
            print(str(e))
            return
        data = raw_data[1:]
        records = []
        for i, row in enumerate(data):
            record = ['E' + str(i+1).zfill(6)] + row + ['1111']
            records.append(record)
        self.c.executemany("insert into {}EMPLOYEES values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)".format(self.schema), records)
        
        ##: Generate records for the Tasks Table
        try:
            with open('tasks.csv', 'r') as f:
                reader = csv.reader(f)
                raw_data = [row for row in reader]
        except Exception as e:
            print(str(e))
            return    
        self.c.executemany("insert into TASKS(Name, Role) values (?, ?)", raw_data[1:])    

        self.conn.commit()

    def retrieveTasks(self):        
        self.c.execute("select Name, Role from TASKS".format(self.schema))       
        records = self.c.fetchall()
        return records

    def retrieveTitles(self):        
        self.c.execute("select distinct Title from EMPLOYEES".format(self.schema))       
        records = self.c.fetchall()
        return [r[0] for r in records]
    
    def retrieveEmployees(self):        
        self.c.execute("select EmployeeID,  FirstName, LastName, Address, City, State, Zip, PhoneNumber, Email, \
              Title, Salary, YearJoined from EMPLOYEES".format(self.schema))       
        records = self.c.fetchall()
        data = []
        for rec in records:
            row = list(rec)
            if row[10]!='':
                row[10] = str(int(row[10]))
            data.append(row)
        return data
    
    def find_next_available_employee_id(self):
        """Find the next available employee ID."""
        self.c.execute("select EmployeeID from EMPLOYEES".format(self.schema))      
        records = self.c.fetchall()
          
        ##: Find the maximum number in all IDs
        nums = [int(row[0][1:]) for row in records]
        if len(nums)>0:
            num = max(nums) + 1
        else:
            num = 1
             
        newID = 'E' + str(num).zfill(6)
        return newID
        
    def retrieveEmployee(self, employeeid):        
        self.c.execute("select EmployeeID,  FirstName, LastName, Address, City, State, Zip, PhoneNumber, Email, \
              Title, Salary, YearJoined, Password from EMPLOYEES where EmployeeID = ?".format(self.schema), [employeeid])   
        return self.c.fetchone()      
        
    def insertEmployeeRecord(self, record):    
        pwd = ''
        self.c.execute("insert into {}EMPLOYEES values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)".format(self.schema), record + [pwd])
                
    def updateEmployeeRecord(self, record):
        """ Update employee record"""
        self.c.execute("update EMPLOYEES set FirstName=?, LastName=?, Address=?, City=?, State=?, Zip=?, PhoneNumber=?, Email=?, \
              Title=?, Salary=?, YearJoined=? where EmployeeID = ?".format(self.schema), record[1:]+[record[0]])
        
    def deleteEmployee(self, employeeID):
        """ Delete the record in EMPLOYEE table"""
        if self.retrieveEmployee(employeeID):
            self.c.execute("delete from {}EMPLOYEES where EmployeeID = ?".format(self.schema), [employeeID])
            
    def retrievePassword(self, employeeid):
        """Retrieve password by employee ID"""
        self.c.execute("select Password from {}EMPLOYEES where EmployeeID = ?".format(self.schema), [employeeid]) 
        pwd = self.c.fetchone()
        if pwd:
            return pwd[0]
        else:
            return None
    
    def updatePassword(self, employeeid, pwd):
        """ Update employee password"""
        self.c.execute("update EMPLOYEES set Password=? where EmployeeID = ?".format(self.schema), [pwd, employeeid])
        
    def insertAttendanceRecords(self, records):
        """Insert attendance records in database"""
        
        for record in records:
            row = (record[0], record[1].strftime('%Y-%m-%d %H:%M:%S'))
            self.c.execute("insert into {}ATTENDANCE values (?, ?)".format(self.schema), row)        
    
    def updateScheduleRecord(self, record):        
        """Update schedule record."""
        
        employeeID = record[0]
        self.c.execute("select EmployeeID from {}SCHEDULE where EmployeeID = ?".format(self.schema), [employeeID])
        if self.c.fetchone(): 
            self.c.execute("update SCHEDULE set WeekStartDate=?, SunAM=?, SunPM=?, MonAM=?, MonPM=?, TueAM=?, TuePM=?, WedAM=?, WedPM=?, \
            ThuAM=?, ThuPM=?, FriAM=?, FriPM=?, SatAM=?, SatPM=? where EmployeeID=?".format(self.schema), record[1:]+[record[0]])
        else:    
            self.c.execute("insert into {}SCHEDULE values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)".format(self.schema), record)    
    
    def retrieveScheduleRecord(self, employeeid):        
        self.c.execute("select * from SCHEDULE where EmployeeID = ?".format(self.schema), [employeeid])   
        return self.c.fetchone()      
    
    def deleteAttendanceRecords(self):
        self.c.execute("delete from {}ATTENDANCE".format(self.schema))
                
if __name__ == '__main__':
    
#     date1 = datetime(2016, 12, 1)
#     date2 = datetime(2016, 12, 19)
#     data = DataCenter.get_intraday_data('AAPL', date1, date2, 'IntradayGoogle', '5 min')
    
    date1 = datetime(2015, 11, 10)
    date2 = datetime(2015, 11, 17)
    data = DataCenter.get_intraday_data('TSS', date1, date2, 'IntradayGoogle', '5 min')
        
    dataDay = DataCenter.aggregate_intraday_data(data, '5 min')

#     OptionData.get_option_data('AAPL')
#     Utility.create_symbol_list_all()
#     AlphaVantageData.get_intraday_data('MSFT')
#     NetFondData.get_intraday_data('')
# 
#     DataCollector.collect_intraday_data()
#     DataCollector.collect_option_data()
    
    print('Program Finished!!!')        