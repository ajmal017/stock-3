import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter, WeekdayLocator, DayLocator, MONDAY, date2num
from mpl_finance import quotes_historical_yahoo_ohlc, candlestick_ohlc
from _datetime import datetime, timedelta
from dataCenter import DataCenter 

# (Year, month, day) tuples suffice as args for quotes_historical_yahoo
# date1 = (2004, 2, 1)
# date2 = (2004, 4, 12)
# quotes = quotes_historical_yahoo_ohlc('INTC', date1, date2)

date1 = datetime(2016, 12, 1)
date2 = datetime(2016, 12, 19)
data = DataCenter.get_intraday_data('AAPL', date1, date2, 'IntradayGoogle')
dataDay = DataCenter.aggregate_intraday_data(data, timedelta(days=1))
# dataDay = DataCenter.aggregate_intraday_data(data, timedelta(minutes=60))
quotes = [[date2num(rec[0])]+rec[1:] for rec in dataDay]

mondays = WeekdayLocator(MONDAY)        # major ticks on the mondays
alldays = DayLocator()              # minor ticks on the days
weekFormatter = DateFormatter('%b %d')  # e.g., Jan 12
dayFormatter = DateFormatter('%d')      # e.g., 12

if len(quotes) == 0:
    raise SystemExit

fig, ax = plt.subplots()
fig.subplots_adjust(bottom=0.2)
ax.xaxis.set_major_locator(mondays)
ax.xaxis.set_minor_locator(alldays)
ax.xaxis.set_major_formatter(weekFormatter)
#ax.xaxis.set_minor_formatter(dayFormatter)

#plot_day_summary(ax, quotes, ticksize=3)
candlestick_ohlc(ax, quotes, width=0.6)

ax.xaxis_date()
ax.autoscale_view()
plt.setp(plt.gca().get_xticklabels(), rotation=45, horizontalalignment='right')

plt.show()
