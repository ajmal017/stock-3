"""
A collection of functions for collecting, analyzing and plotting
financial data.   User contributions welcome!

"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

# import six
# from six.moves import xrange, zip

import contextlib
import os
import warnings
# from six.moves.urllib.request import urlopen

import datetime

import numpy as np

from matplotlib import colors as mcolors, verbose, get_cachedir
from matplotlib.dates import date2num
from matplotlib.cbook import iterable, mkdirs
from matplotlib.collections import LineCollection, PolyCollection
from matplotlib.lines import Line2D, TICKLEFT, TICKRIGHT
from matplotlib.patches import Rectangle
from matplotlib.transforms import Affine2D
from matplotlib import gridspec

import matplotlib.pyplot as plt 
from dataCenter import DataCenter
from _datetime import timedelta

# 
# if six.PY3:
#     import hashlib
# 
#     def md5(x):
#         return hashlib.md5(x.encode())
# else:
#     from hashlib import md5
# 
# cachedir = get_cachedir()
# # cachedir will be None if there is no writable directory.
# if cachedir is not None:
#     cachedir = os.path.join(cachedir, 'finance.cache')
# else:
#     # Should only happen in a restricted environment (such as Google App
#     # Engine). Deal with this gracefully by not caching finance data.
#     cachedir = None


stock_dt_ohlc = np.dtype([
    (str('date'), object),
    (str('year'), np.int16),
    (str('month'), np.int8),
    (str('day'), np.int8),
    (str('d'), np.float),     # mpl datenum
    (str('open'), np.float),
    (str('high'), np.float),
    (str('low'), np.float),
    (str('close'), np.float),
    (str('volume'), np.float),
    (str('aclose'), np.float)])


stock_dt_ochl = np.dtype(
    [(str('date'), object),
     (str('year'), np.int16),
     (str('month'), np.int8),
     (str('day'), np.int8),
     (str('d'), np.float),     # mpl datenum
     (str('open'), np.float),
     (str('close'), np.float),
     (str('high'), np.float),
     (str('low'), np.float),
     (str('volume'), np.float),
     (str('aclose'), np.float)])




def _plot_ohlc_ax(ax, quotes, width=0.2, colorup='k', colordown='r',
                 alpha=1.0, ochl=True):
    
    OFFSET = width / 2.0    
    lines = []
    for i, (t, open, high, low, close, volume)  in enumerate(quotes):

        if close >= open:
            color = colorup
            lower = open
            height = close - open
        else:
            color = colordown
            lower = close
            height = open - close

        vline = Line2D(
            xdata=(i, i), ydata=(low, high),
            color=color,
            linewidth=1,
            antialiased=True,
        )
        hline_open = Line2D(
            xdata=(i-OFFSET, i), ydata=(open, open),
#             color=color,
            linewidth=0.5,
            antialiased=True,
        )        
        hline_close = Line2D(
            xdata=(i, i+OFFSET), ydata=(close, close),
#             color=color,
            linewidth=1,
            antialiased=True,
        )

        lines.append(vline)
        lines.append(hline_open)
        lines.append(hline_close)
        ax.add_line(vline)
        ax.add_line(hline_open)
        ax.add_line(hline_close)

    ax.autoscale_view()
    return lines

def _plot_ohlc_ax_time(ax, quotes, width=0.2, colorup='k', colordown='r',
                 alpha=1.0, ochl=True):
    
    dt = quotes[1][0]-quotes[0][0]
    OFFSET = dt * width / 2.0
    
    lines = []
    patches = []
    for t, open, high, low, close, volume  in quotes:

        if close >= open:
            color = colorup
            lower = open
            height = close - open
        else:
            color = colordown
            lower = close
            height = open - close

        vline = Line2D(
            xdata=(t, t), ydata=(low, high),
            color=color,
            linewidth=0.5,
            antialiased=True,
        )
        hline_open = Line2D(
            xdata=(t-OFFSET, t), ydata=(open, open),
#             color=color,
            linewidth=0.5,
            antialiased=True,
        )        
        hline_close = Line2D(
            xdata=(t, t+OFFSET), ydata=(close, close),
#             color=color,
            linewidth=0.5,
            antialiased=True,
        )

#         rect = Rectangle(
#             xy=(t - OFFSET, lower),
#             width=width,
#             height=height,
#             facecolor=color,
#             edgecolor=color,
#         )
#         rect.set_alpha(alpha)

        lines.append(vline)
        lines.append(hline_open)
        lines.append(hline_close)
        ax.add_line(vline)
        ax.add_line(hline_open)
        ax.add_line(hline_close)
        
#         patches.append(rect)
#         ax.add_patch(rect)
    ax.autoscale_view()
    return lines


def _plot_volume_ax(ax, quotes, width=0.2, colorup='g', colordown='r',
                 alpha=1.0, ochl=True):
    
    OFFSET = width / 2.0
    
    bars = []
    pre_close = 0
    for i, (t, open, high, low, close, volume) in enumerate(quotes):

        if close >= pre_close:
            color = colorup
        else:
            color = colordown
        pre_close = close
        
        rect = Rectangle(
            xy=(i - OFFSET, 0),
            width=width,
            height=volume,
            facecolor=color,
            edgecolor=color,
        )
        rect.set_alpha(alpha)

        bars.append(rect)
        ax.add_patch(rect)

    ax.autoscale_view()
    ax.set_ylim(bottom=0)
    
#     (xticks, xticklabels, endTickLabel) = _get_time_axis_ticks(quotes)
#     xticks.append(ax.get_xlim()[1])
#     xticklabels.append(endTickLabel)
#     ax.set_xticks(xticks)
#     ax.set_xticklabels(xticklabels)
    
    return bars

def _plot_volume_ax_time(ax, quotes, width=0.2, colorup='k', colordown='r',
                 alpha=1.0, ochl=True):
    
    
    closes = [r[4] for r in quotes]
    volumes =  np.array([r[5] for r in quotes])
    dates = np.array([r[0] for r in quotes])

    deltas = np.zeros_like(closes)
    deltas[1:] = np.diff(closes)
    up = deltas > 0
 
    dt = quotes[1][0]-quotes[0][0]
    barwidth = dt * width
    ax.bar(dates[up], volumes[up], width, color=colorup, label='_nolegend_')
    ax.bar(dates[~up], volumes[~up], width, color=colordown, label='_nolegend_')
    
def _plot_volume_ax_date2num(ax, quotes, width=0.2, colorup='k', colordown='r',
                 alpha=1.0, ochl=True):
    closes = [r[4] for r in quotes]
    volumes =  np.array([r[5] for r in quotes])
    dates = np.array([r[0] for r in quotes])

    deltas = np.zeros_like(closes)
    deltas[1:] = np.diff(closes)
    up = deltas > 0
 
    ax.bar(dates[up], volumes[up], color=colorup, label='_nolegend_')
    ax.bar(dates[~up], volumes[~up], color=colordown, label='_nolegend_')

def _get_time_axis_ticks(quotes):
    dates = np.array([r[0] for r in quotes])
    dt = dates[1] - dates[0]
    MAXTICKS = 20  ##: can't be too crowded
    MAXTICKS = 2000  ##: can't be too crowded
#     if len(dates) <= MAXTICKS:
#         ticks = range(len(dates))
#         if dt >= timedelta(days=1):
#             ticklabels = [d.strftime('%m/%d') for d in dates]
#             endTickLabel = dates[-1].strftime('%Y')
#         else:
#             ticklabels = [d.strftime('%H:%M') for d in dates]
#             endTickLabel = dates[-1].strftime('%Y/%m/%d')
#             
#         return (ticks, ticklabels, endTickLabel)
    
    ticks = [i for i in range(len(dates))]
    if dt >= timedelta(days=1):
        ticklabels = [d.strftime('%m/%d') for d in dates]
        endTickLabel = dates[-1].strftime('%Y')        
    else:
        ticklabels = [d.strftime('%H:%M') for d in dates]
        endTickLabel = dates[-1].strftime('%Y/%m/%d')
            
    
    if dt >= timedelta(days=1):
        ticklabels[0] += '\n'+ dates[0].strftime('%Y')  
        for i in range(1, len(dates)):
            if dates[i].year!=dates[i-1].year:
                ticklabels[i] += '\n'+ dates[i].strftime('%Y')  
    else:
        ticklabels[0] += '\n'+ dates[0].strftime('%Y/%m/%d')  
        for i in range(1, len(dates)):
            if dates[i].day!=dates[i-1].day:
                ticklabels[i] += '\n'+ dates[i].strftime('%Y/%m/%d')  
    
    return (ticks, ticklabels, endTickLabel)
     
def plot_price_volume(fig, quotes):

    left, width = 0.1, 0.8
    rect1 = [left, 0.3, width, 0.7]
    rect2 = [left, 0.1, width, 0.2]
    barwidth = 0.6
    ax1 = fig.add_axes(rect1)  # left, bottom, width, height
    ax2 = fig.add_axes(rect2, sharex=ax1)
    
    lines = _plot_ohlc_ax(ax1, quotes)
    bars = _plot_volume_ax(ax2, quotes, width = barwidth)
    
    (xticks, xticklabels, endTickLabel) = _get_time_axis_ticks(quotes)
    xticks.append(ax2.get_xlim()[1])
    xticklabels.append(endTickLabel)
    ax2.set_xticks(xticks)
    ax2.set_xticklabels(xticklabels)
    ax2.set_xlim(left=-barwidth/2)
    ##: Plot grid
    sepLocs = [i for i, tlabel in enumerate(xticklabels) if '\n' in tlabel]
    for loc in sepLocs:
        ax1.axvline(loc-barwidth/2, linestyle='--', color='k', linewidth=0.5) # vertical lines
        ax2.axvline(loc-barwidth/2, linestyle='--', color='k', linewidth=0.5) # vertical lines

    
    
    
#     fig, (ax1, ax2) = fig.subplots(2,1, gridspec_kw = {'height_ratios':[3, 1]})
#     ax1 = fig.subplot2grid((4, 1), (0, 0), rowspan=3)
#     ax2 = fig.subplot2grid((4, 1), (0, 1), rowspan=1)
    
#     fig.gca().clear()
#     fig.clf()


#     axes = fig.axes
#     if len(axes)==2:
#         ax1 = axes[0]
#         ax2 = axes[1]
#         ax1.clear()
#         ax2.clear()
#     else:
#         ax1 = fig.add_subplot(211)
#         ax2 = fig.add_subplot(212)

#     ax1 = fig.add_subplot(211)
#     ax2 = fig.add_subplot(212)

    
#     fig.tick_params(
#     axis='x',          # changes apply to the x-axis
#     which='both',      # both major and minor ticks are affected
#     bottom='off',      # ticks along the bottom edge are off
#     top='off',         # ticks along the top edge are off
#     labelbottom='off') # labels along the bottom edge are off
    
#     fig.show()

#     fillcolor = 'darkgoldenrod'
#     volumes = [cls*vol/1e6 for (cls, vol) in zip(closes, volumes)] # dollar volume in millions
#     vmax = max(volumes)
#     poly = axt.fill_between(dates, volumes, 0, label='Volume', facecolor=fillcolor, edgecolor=fillcolor)
#     axt.set_ylim(0, 5*vmax)
#     axt.set_yticks([])
#     
def plot_price_volume_line(ax, quotes, width=4,
                 colorup='k', colordown='r',
                 alpha=0.75):
    
    dates = [r[0] for r in quotes]
    opens = [r[1] for r in quotes]
    highs = [r[2] for r in quotes]
    lows = [r[3] for r in quotes]
    closes = [r[4] for r in quotes]
    volumes = [r[5] for r in quotes]
    
    textsize = 9
    left, width = 0.1, 0.8
    rect1 = [left, 0.7, width, 0.2]
    rect2 = [left, 0.3, width, 0.4]
    axt = ax.twinx()
    ax.plot(dates, closes)


    fillcolor = 'darkgoldenrod'
    volumes = [cls*vol/1e6 for (cls, vol) in zip(closes, volumes)] # dollar volume in millions
    vmax = max(volumes)
    poly = axt.fill_between(dates, volumes, 0, label='Volume', facecolor=fillcolor, edgecolor=fillcolor)
    axt.set_ylim(0, 5*vmax)
    axt.set_yticks([])
    
# 
# # plot the price and volume data
# dx = ropen - rclose
# low = rlow + dx
# high = rhigh + dx
# 
# deltas = np.zeros_like(prices)
# deltas[1:] = np.diff(prices)
# up = deltas > 0
# 
# ax2.vlines(rdate[up], low[up], high[up], color='black', label='_nolegend_')
# ax2.vlines(rdate[~up], low[~up], high[~up], color='black', label='_nolegend_')
# ma20 = moving_average(prices, 20, type='simple')
# ma200 = moving_average(prices, 200, type='simple')
# 
# linema20, = ax2.plot(rdate, ma20, color='blue', lw=2, label='MA (20)')
# linema200, = ax2.plot(rdate, ma200, color='red', lw=2, label='MA (200)')
# 
# 
# # last = r[-1]
# s = '%s O:%1.2f H:%1.2f L:%1.2f C:%1.2f, V:%1.1fM Chg:%+1.2f' % (
#     datetime.today().strftime('%d-%b-%Y'),
#     ropen[-1], rhigh[-1],
#     rlow[-1], rclose[-1],
#     rvolume[-1]*1e-6,
#     rclose[-1] - ropen[-1])
# t4 = ax2.text(0.3, 0.9, s, transform=ax2.transAxes, fontsize=textsize)
# 
# props = font_manager.FontProperties(size=10)
# leg = ax2.legend(loc='center left', shadow=True, fancybox=True, prop=props)
# leg.get_frame().set_alpha(0.5)
# 
# 
# volume = (rclose*rvolume)/1e6  # dollar volume in millions
# vmax = volume.max()
# poly = ax2t.fill_between(rdate, volume, 0, label='Volume', facecolor=fillcolor, edgecolor=fillcolor)
# ax2t.set_ylim(0, 5*vmax)
# ax2t.set_yticks([])
# 
# 
# 
# 
# 
#     ax.rc('axes', grid=True)
#     ax.rc('grid', color='0.75', linestyle='-', linewidth=0.5)
# 
#     textsize = 9
#     left, width = 0.1, 0.8
#     rect1 = [left, 0.7, width, 0.2]
#     rect2 = [left, 0.3, width, 0.4]
#     rect3 = [left, 0.1, width, 0.2]
# 
# 
# fig = plt.figure(facecolor='white')
# axescolor = '#f6f6f6'  # the axes background color
# 
# ax1 = fig.add_axes(rect1, facecolor=axescolor)  # left, bottom, width, height
# ax2 = fig.add_axes(rect2, facecolor=axescolor, sharex=ax1)
# ax2t = ax2.twinx()
# ax3 = fig.add_axes(rect3, facecolor=axescolor, sharex=ax1)
# 
# 
# # ropen = [r[1] for r in quotes]
# # rhigh = [r[2] for r in quotes]
# # rlow = [r[3] for r in quotes]
# # rclose = [r[4] for r in quotes]
# # rdate = [r[0] for r in quotes]
# # rvolume = [r[5] for r in quotes]
# 
# ropen = np.array([r[1] for r in quotes])
# rhigh = np.array([r[2] for r in quotes])
# rlow = np.array([r[3] for r in quotes])
# rclose = np.array([r[4] for r in quotes])
# rdate = np.array([r[0] for r in quotes])
# rvolume = np.array([r[5] for r in quotes])
# 
# # plot the relative strength indicator
# # prices = r.adj_close
# prices = ropen
# 
# rsi = relative_strength(prices)
# fillcolor = 'darkgoldenrod'
# 
# ax1.plot(rdate, rsi, color=fillcolor)
# ax1.axhline(70, color=fillcolor)
# ax1.axhline(30, color=fillcolor)
# ax1.fill_between(rdate, rsi, 70, where=(rsi >= 70), facecolor=fillcolor, edgecolor=fillcolor)
# ax1.fill_between(rdate, rsi, 30, where=(rsi <= 30), facecolor=fillcolor, edgecolor=fillcolor)
# ax1.text(0.6, 0.9, '>70 = overbought', va='top', transform=ax1.transAxes, fontsize=textsize)
# ax1.text(0.6, 0.1, '<30 = oversold', transform=ax1.transAxes, fontsize=textsize)
# ax1.set_ylim(0, 100)
# ax1.set_yticks([30, 70])
# ax1.text(0.025, 0.95, 'RSI (14)', va='top', transform=ax1.transAxes, fontsize=textsize)
# ax1.set_title('%s daily' % ticker)
# 
# # plot the price and volume data
# dx = ropen - rclose
# low = rlow + dx
# high = rhigh + dx
# 
# deltas = np.zeros_like(prices)
# deltas[1:] = np.diff(prices)
# up = deltas > 0
# ax2.vlines(rdate[up], low[up], high[up], color='black', label='_nolegend_')
# ax2.vlines(rdate[~up], low[~up], high[~up], color='black', label='_nolegend_')
# ma20 = moving_average(prices, 20, type='simple')
# ma200 = moving_average(prices, 200, type='simple')
# 
# linema20, = ax2.plot(rdate, ma20, color='blue', lw=2, label='MA (20)')
# linema200, = ax2.plot(rdate, ma200, color='red', lw=2, label='MA (200)')
# 
# 
# # last = r[-1]
# s = '%s O:%1.2f H:%1.2f L:%1.2f C:%1.2f, V:%1.1fM Chg:%+1.2f' % (
#     datetime.today().strftime('%d-%b-%Y'),
#     ropen[-1], rhigh[-1],
#     rlow[-1], rclose[-1],
#     rvolume[-1]*1e-6,
#     rclose[-1] - ropen[-1])
# t4 = ax2.text(0.3, 0.9, s, transform=ax2.transAxes, fontsize=textsize)
# 
# props = font_manager.FontProperties(size=10)
# leg = ax2.legend(loc='center left', shadow=True, fancybox=True, prop=props)
# leg.get_frame().set_alpha(0.5)
# 
# 
# volume = (rclose*rvolume)/1e6  # dollar volume in millions
# vmax = volume.max()
# poly = ax2t.fill_between(rdate, volume, 0, label='Volume', facecolor=fillcolor, edgecolor=fillcolor)
# ax2t.set_ylim(0, 5*vmax)
# ax2t.set_yticks([])
# 
# 
# # compute the MACD indicator
# fillcolor = 'darkslategrey'
# nslow = 26
# nfast = 12
# nema = 9
# emaslow, emafast, macd = moving_average_convergence(prices, nslow=nslow, nfast=nfast)
# ema9 = moving_average(macd, nema, type='exponential')
# ax3.plot(rdate, macd, color='black', lw=2)
# ax3.plot(rdate, ema9, color='blue', lw=1)
# ax3.fill_between(rdate, macd - ema9, 0, alpha=0.5, facecolor=fillcolor, edgecolor=fillcolor)
# 
# 
# ax3.text(0.025, 0.95, 'MACD (%d, %d, %d)' % (nfast, nslow, nema), va='top',
#          transform=ax3.transAxes, fontsize=textsize)
# 
# #ax3.set_yticks([])
# # turn off upper axis tick labels, rotate the lower ones, etc
# for ax in ax1, ax2, ax2t, ax3:
#     if ax != ax3:
#         for label in ax.get_xticklabels():
#             label.set_visible(False)
#     else:
#         for label in ax.get_xticklabels():
#             label.set_rotation(30)
#             label.set_horizontalalignment('right')
# 
#     ax.fmt_xdata = mdates.DateFormatter('%Y-%m-%d')



def parse_yahoo_historical_ochl(fh, adjusted=True, asobject=False):
    """Parse the historical data in file handle fh from yahoo finance.

    Parameters
    ----------

    adjusted : bool
      If True (default) replace open, close, high, low prices with
      their adjusted values. The adjustment is by a scale factor, S =
      adjusted_close/close. Adjusted prices are actual prices
      multiplied by S.

      Volume is not adjusted as it is already backward split adjusted
      by Yahoo. If you want to compute dollars traded, multiply volume
      by the adjusted close, regardless of whether you choose adjusted
      = True|False.


    asobject : bool or None
      If False (default for compatibility with earlier versions)
      return a list of tuples containing

        d, open, close, high, low,  volume

      If None (preferred alternative to False), return
      a 2-D ndarray corresponding to the list of tuples.

      Otherwise return a numpy recarray with

        date, year, month, day, d, open, close, high, low,
        volume, adjusted_close

      where d is a floating poing representation of date,
      as returned by date2num, and date is a python standard
      library datetime.date instance.

      The name of this kwarg is a historical artifact.  Formerly,
      True returned a cbook Bunch
      holding 1-D ndarrays.  The behavior of a numpy recarray is
      very similar to the Bunch.

    """
    return _parse_yahoo_historical(fh, adjusted=adjusted, asobject=asobject,
                           ochl=True)


def parse_yahoo_historical_ohlc(fh, adjusted=True, asobject=False):
    """Parse the historical data in file handle fh from yahoo finance.

    Parameters
    ----------

    adjusted : bool
      If True (default) replace open, high, low, close prices with
      their adjusted values. The adjustment is by a scale factor, S =
      adjusted_close/close. Adjusted prices are actual prices
      multiplied by S.

      Volume is not adjusted as it is already backward split adjusted
      by Yahoo. If you want to compute dollars traded, multiply volume
      by the adjusted close, regardless of whether you choose adjusted
      = True|False.


    asobject : bool or None
      If False (default for compatibility with earlier versions)
      return a list of tuples containing

        d, open, high, low, close, volume

      If None (preferred alternative to False), return
      a 2-D ndarray corresponding to the list of tuples.

      Otherwise return a numpy recarray with

        date, year, month, day, d, open, high, low,  close,
        volume, adjusted_close

      where d is a floating poing representation of date,
      as returned by date2num, and date is a python standard
      library datetime.date instance.

      The name of this kwarg is a historical artifact.  Formerly,
      True returned a cbook Bunch
      holding 1-D ndarrays.  The behavior of a numpy recarray is
      very similar to the Bunch.
    """
    return _parse_yahoo_historical(fh, adjusted=adjusted, asobject=asobject,
                           ochl=False)


def _parse_yahoo_historical(fh, adjusted=True, asobject=False,
                           ochl=True):
    """Parse the historical data in file handle fh from yahoo finance.


    Parameters
    ----------

    adjusted : bool
      If True (default) replace open, high, low, close prices with
      their adjusted values. The adjustment is by a scale factor, S =
      adjusted_close/close. Adjusted prices are actual prices
      multiplied by S.

      Volume is not adjusted as it is already backward split adjusted
      by Yahoo. If you want to compute dollars traded, multiply volume
      by the adjusted close, regardless of whether you choose adjusted
      = True|False.


    asobject : bool or None
      If False (default for compatibility with earlier versions)
      return a list of tuples containing

        d, open, high, low, close, volume

       or

        d, open, close, high, low, volume

      depending on `ochl`

      If None (preferred alternative to False), return
      a 2-D ndarray corresponding to the list of tuples.

      Otherwise return a numpy recarray with

        date, year, month, day, d, open, high, low, close,
        volume, adjusted_close

      where d is a floating poing representation of date,
      as returned by date2num, and date is a python standard
      library datetime.date instance.

      The name of this kwarg is a historical artifact.  Formerly,
      True returned a cbook Bunch
      holding 1-D ndarrays.  The behavior of a numpy recarray is
      very similar to the Bunch.

    ochl : bool
        Selects between ochl and ohlc ordering.
        Defaults to True to preserve original functionality.

    """
    if ochl:
        stock_dt = stock_dt_ochl
    else:
        stock_dt = stock_dt_ohlc

    results = []

    #    datefmt = '%Y-%m-%d'
    fh.readline()  # discard heading
    for line in fh:

        vals = line.split(',')
        if len(vals) != 7:
            continue      # add warning?
        datestr = vals[0]
        #dt = datetime.date(*time.strptime(datestr, datefmt)[:3])
        # Using strptime doubles the runtime. With the present
        # format, we don't need it.
        dt = datetime.date(*[int(val) for val in datestr.split('-')])
        dnum = date2num(dt)
        open, high, low, close = [float(val) for val in vals[1:5]]
        volume = float(vals[5])
        aclose = float(vals[6])
        if ochl:
            results.append((dt, dt.year, dt.month, dt.day,
                            dnum, open, close, high, low, volume, aclose))

        else:
            results.append((dt, dt.year, dt.month, dt.day,
                            dnum, open, high, low, close, volume, aclose))
    results.reverse()
    d = np.array(results, dtype=stock_dt)
    if adjusted:
        scale = d['aclose'] / d['close']
        scale[np.isinf(scale)] = np.nan
        d['open'] *= scale
        d['high'] *= scale
        d['low'] *= scale
        d['close'] *= scale

    if not asobject:
        # 2-D sequence; formerly list of tuples, now ndarray
        ret = np.zeros((len(d), 6), dtype=float)
        ret[:, 0] = d['d']
        if ochl:
            ret[:, 1] = d['open']
            ret[:, 2] = d['close']
            ret[:, 3] = d['high']
            ret[:, 4] = d['low']
        else:
            ret[:, 1] = d['open']
            ret[:, 2] = d['high']
            ret[:, 3] = d['low']
            ret[:, 4] = d['close']
        ret[:, 5] = d['volume']
        if asobject is None:
            return ret
        return [tuple(row) for row in ret]

    return d.view(np.recarray)  # Close enough to former Bunch return


def plot_day_summary_oclh(ax, quotes, ticksize=3,
                     colorup='k', colordown='r',
                     ):
    """Plots day summary

        Represent the time, open, close, high, low as a vertical line
        ranging from low to high.  The left tick is the open and the right
        tick is the close.



    Parameters
    ----------
    ax : `Axes`
        an `Axes` instance to plot to
    quotes : sequence of (time, open, close, high, low, ...) sequences
        data to plot.  time must be in float date format - see date2num
    ticksize : int
        open/close tick marker in points
    colorup : color
        the color of the lines where close >= open
    colordown : color
        the color of the lines where close <  open

    Returns
    -------
    lines : list
        list of tuples of the lines added (one tuple per quote)
    """
    return _plot_day_summary(ax, quotes, ticksize=ticksize,
                     colorup=colorup, colordown=colordown,
                     ochl=True)


def plot_day_summary_ohlc(ax, quotes, ticksize=3,
                     colorup='k', colordown='r',
                      ):
    """Plots day summary

        Represent the time, open, high, low, close as a vertical line
        ranging from low to high.  The left tick is the open and the right
        tick is the close.



    Parameters
    ----------
    ax : `Axes`
        an `Axes` instance to plot to
    quotes : sequence of (time, open, high, low, close, ...) sequences
        data to plot.  time must be in float date format - see date2num
    ticksize : int
        open/close tick marker in points
    colorup : color
        the color of the lines where close >= open
    colordown : color
        the color of the lines where close <  open

    Returns
    -------
    lines : list
        list of tuples of the lines added (one tuple per quote)
    """
    return _plot_day_summary(ax, quotes, ticksize=ticksize,
                     colorup=colorup, colordown=colordown,
                     ochl=False)


def _plot_day_summary(ax, quotes, ticksize=3,
                     colorup='k', colordown='r',
                     ochl=True
                     ):
    """Plots day summary


        Represent the time, open, high, low, close as a vertical line
        ranging from low to high.  The left tick is the open and the right
        tick is the close.



    Parameters
    ----------
    ax : `Axes`
        an `Axes` instance to plot to
    quotes : sequence of quote sequences
        data to plot.  time must be in float date format - see date2num
        (time, open, high, low, close, ...) vs
        (time, open, close, high, low, ...)
        set by `ochl`
    ticksize : int
        open/close tick marker in points
    colorup : color
        the color of the lines where close >= open
    colordown : color
        the color of the lines where close <  open
    ochl: bool
        argument to select between ochl and ohlc ordering of quotes

    Returns
    -------
    lines : list
        list of tuples of the lines added (one tuple per quote)
    """
    # unfortunately this has a different return type than plot_day_summary2_*
    lines = []
    for q in quotes:
        if ochl:
            t, open, close, high, low = q[:5]
        else:
            t, open, high, low, close = q[:5]

        if close >= open:
            color = colorup
        else:
            color = colordown

        vline = Line2D(xdata=(t, t), ydata=(low, high),
                       color=color,
                       antialiased=False,   # no need to antialias vert lines
                       )

        oline = Line2D(xdata=(t, t), ydata=(open, open),
                       color=color,
                       antialiased=False,
                       marker=TICKLEFT,
                       markersize=ticksize,
                       )

        cline = Line2D(xdata=(t, t), ydata=(close, close),
                       color=color,
                       antialiased=False,
                       markersize=ticksize,
                       marker=TICKRIGHT)

        lines.extend((vline, oline, cline))
        ax.add_line(vline)
        ax.add_line(oline)
        ax.add_line(cline)

    ax.autoscale_view()

    return lines


def candlestick_ochl(ax, quotes, width=0.2, colorup='k', colordown='r',
                alpha=1.0):

    """
    Plot the time, open, close, high, low as a vertical line ranging
    from low to high.  Use a rectangular bar to represent the
    open-close span.  If close >= open, use colorup to color the bar,
    otherwise use colordown

    Parameters
    ----------
    ax : `Axes`
        an Axes instance to plot to
    quotes : sequence of (time, open, close, high, low, ...) sequences
        As long as the first 5 elements are these values,
        the record can be as long as you want (e.g., it may store volume).

        time must be in float days format - see date2num

    width : float
        fraction of a day for the rectangle width
    colorup : color
        the color of the rectangle where close >= open
    colordown : color
         the color of the rectangle where close <  open
    alpha : float
        the rectangle alpha level

    Returns
    -------
    ret : tuple
        returns (lines, patches) where lines is a list of lines
        added and patches is a list of the rectangle patches added

    """
    return _candlestick(ax, quotes, width=width, colorup=colorup,
                        colordown=colordown,
                        alpha=alpha, ochl=True)


def candlestick_ohlc(ax, quotes, width=0.2, colorup='k', colordown='r',
                alpha=1.0):

    """
    Plot the time, open, high, low, close as a vertical line ranging
    from low to high.  Use a rectangular bar to represent the
    open-close span.  If close >= open, use colorup to color the bar,
    otherwise use colordown

    Parameters
    ----------
    ax : `Axes`
        an Axes instance to plot to
    quotes : sequence of (time, open, high, low, close, ...) sequences
        As long as the first 5 elements are these values,
        the record can be as long as you want (e.g., it may store volume).

        time must be in float days format - see date2num

    width : float
        fraction of a day for the rectangle width
    colorup : color
        the color of the rectangle where close >= open
    colordown : color
         the color of the rectangle where close <  open
    alpha : float
        the rectangle alpha level

    Returns
    -------
    ret : tuple
        returns (lines, patches) where lines is a list of lines
        added and patches is a list of the rectangle patches added

    """
    return _candlestick(ax, quotes, width=width, colorup=colorup,
                        colordown=colordown,
                        alpha=alpha, ochl=False)


def _candlestick(ax, quotes, width=0.2, colorup='k', colordown='r',
                 alpha=1.0, ochl=True):

    """
    Plot the time, open, high, low, close as a vertical line ranging
    from low to high.  Use a rectangular bar to represent the
    open-close span.  If close >= open, use colorup to color the bar,
    otherwise use colordown

    Parameters
    ----------
    ax : `Axes`
        an Axes instance to plot to
    quotes : sequence of quote sequences
        data to plot.  time must be in float date format - see date2num
        (time, open, high, low, close, ...) vs
        (time, open, close, high, low, ...)
        set by `ochl`
    width : float
        fraction of a day for the rectangle width
    colorup : color
        the color of the rectangle where close >= open
    colordown : color
         the color of the rectangle where close <  open
    alpha : float
        the rectangle alpha level
    ochl: bool
        argument to select between ochl and ohlc ordering of quotes

    Returns
    -------
    ret : tuple
        returns (lines, patches) where lines is a list of lines
        added and patches is a list of the rectangle patches added

    """

    OFFSET = width / 2.0

    lines = []
    patches = []
    for q in quotes:
        if ochl:
            t, open, close, high, low = q[:5]
        else:
            t, open, high, low, close = q[:5]

        if close >= open:
            color = colorup
            lower = open
            height = close - open
        else:
            color = colordown
            lower = close
            height = open - close

        vline = Line2D(
            xdata=(t, t), ydata=(low, high),
            color=color,
            linewidth=0.5,
            antialiased=True,
        )

        rect = Rectangle(
            xy=(t - OFFSET, lower),
            width=width,
            height=height,
            facecolor=color,
            edgecolor=color,
        )
        rect.set_alpha(alpha)

        lines.append(vline)
        patches.append(rect)
        ax.add_line(vline)
        ax.add_patch(rect)
    ax.autoscale_view()

    return lines, patches


def _check_input(opens, closes, highs, lows, miss=-1):
    """Checks that *opens*, *highs*, *lows* and *closes* have the same length.
    NOTE: this code assumes if any value open, high, low, close is
    missing (*-1*) they all are missing

    Parameters
    ----------
    ax : `Axes`
        an Axes instance to plot to
    opens : sequence
        sequence of opening values
    highs : sequence
        sequence of high values
    lows : sequence
        sequence of low values
    closes : sequence
        sequence of closing values
    miss : int
        identifier of the missing data

    Raises
    ------
    ValueError
        if the input sequences don't have the same length
    """

    def _missing(sequence, miss=-1):
        """Returns the index in *sequence* of the missing data, identified by
        *miss*

        Parameters
        ----------
        sequence :
            sequence to evaluate
        miss :
            identifier of the missing data

        Returns
        -------
        where_miss: numpy.ndarray
            indices of the missing data
        """
        return np.where(np.array(sequence) == miss)[0]

    same_length = len(opens) == len(highs) == len(lows) == len(closes)
    _missopens = _missing(opens)
    same_missing = ((_missopens == _missing(highs)).all() and
                    (_missopens == _missing(lows)).all() and
                    (_missopens == _missing(closes)).all())

    if not (same_length and same_missing):
        msg = ("*opens*, *highs*, *lows* and *closes* must have the same"
               " length. NOTE: this code assumes if any value open, high,"
               " low, close is missing (*-1*) they all must be missing.")
        raise ValueError(msg)


def plot_day_summary2_ochl(ax, opens, closes, highs, lows, ticksize=4,
                          colorup='k', colordown='r',
                          ):

    """Represent the time, open, close, high, low,  as a vertical line
    ranging from low to high.  The left tick is the open and the right
    tick is the close.

    Parameters
    ----------
    ax : `Axes`
        an Axes instance to plot to
    opens : sequence
        sequence of opening values
    closes : sequence
        sequence of closing values
    highs : sequence
        sequence of high values
    lows : sequence
        sequence of low values
    ticksize : int
        size of open and close ticks in points
    colorup : color
        the color of the lines where close >= open
    colordown : color
         the color of the lines where close <  open

    Returns
    -------
    ret : list
        a list of lines added to the axes
    """

    return plot_day_summary2_ohlc(ax, opens, highs, lows, closes, ticksize,
                                 colorup, colordown)


def plot_day_summary2_ohlc(ax, opens, highs, lows, closes, ticksize=4,
                          colorup='k', colordown='r',
                          ):

    """Represent the time, open, high, low, close as a vertical line
    ranging from low to high.  The left tick is the open and the right
    tick is the close.
    *opens*, *highs*, *lows* and *closes* must have the same length.
    NOTE: this code assumes if any value open, high, low, close is
    missing (*-1*) they all are missing

    Parameters
    ----------
    ax : `Axes`
        an Axes instance to plot to
    opens : sequence
        sequence of opening values
    highs : sequence
        sequence of high values
    lows : sequence
        sequence of low values
    closes : sequence
        sequence of closing values
    ticksize : int
        size of open and close ticks in points
    colorup : color
        the color of the lines where close >= open
    colordown : color
         the color of the lines where close <  open

    Returns
    -------
    ret : list
        a list of lines added to the axes
    """

    _check_input(opens, highs, lows, closes)

    rangeSegments = [((i, low), (i, high)) for i, low, high in
                     zip(range(len(lows)), lows, highs) if low != -1]

    # the ticks will be from ticksize to 0 in points at the origin and
    # we'll translate these to the i, close location
    openSegments = [((-ticksize, 0), (0, 0))]

    # the ticks will be from 0 to ticksize in points at the origin and
    # we'll translate these to the i, close location
    closeSegments = [((0, 0), (ticksize, 0))]

    offsetsOpen = [(i, open) for i, open in
                   zip(range(len(opens)), opens) if open != -1]

    offsetsClose = [(i, close) for i, close in
                    zip(range(len(closes)), closes) if close != -1]

    scale = ax.figure.dpi * (1.0 / 72.0)

    tickTransform = Affine2D().scale(scale, 0.0)

    colorup = mcolors.to_rgba(colorup)
    colordown = mcolors.to_rgba(colordown)
    colord = {True: colorup, False: colordown}
    colors = [colord[open < close] for open, close in
              zip(opens, closes) if open != -1 and close != -1]

    useAA = 0,   # use tuple here
    lw = 1,      # and here
    rangeCollection = LineCollection(rangeSegments,
                                     colors=colors,
                                     linewidths=lw,
                                     antialiaseds=useAA,
                                     )

    openCollection = LineCollection(openSegments,
                                    colors=colors,
                                    antialiaseds=useAA,
                                    linewidths=lw,
                                    offsets=offsetsOpen,
                                    transOffset=ax.transData,
                                    )
    openCollection.set_transform(tickTransform)

    closeCollection = LineCollection(closeSegments,
                                     colors=colors,
                                     antialiaseds=useAA,
                                     linewidths=lw,
                                     offsets=offsetsClose,
                                     transOffset=ax.transData,
                                     )
    closeCollection.set_transform(tickTransform)

    minpy, maxx = (0, len(rangeSegments))
    miny = min([low for low in lows if low != -1])
    maxy = max([high for high in highs if high != -1])
    corners = (minpy, miny), (maxx, maxy)
    ax.update_datalim(corners)
    ax.autoscale_view()

    # add these last
    ax.add_collection(rangeCollection)
    ax.add_collection(openCollection)
    ax.add_collection(closeCollection)
    return rangeCollection, openCollection, closeCollection


def candlestick2_ochl(ax, opens, closes, highs, lows,  width=4,
                 colorup='k', colordown='r',
                 alpha=0.75,
                 ):
    """Represent the open, close as a bar line and high low range as a
    vertical line.

    Preserves the original argument order.


    Parameters
    ----------
    ax : `Axes`
        an Axes instance to plot to
    opens : sequence
        sequence of opening values
    closes : sequence
        sequence of closing values
    highs : sequence
        sequence of high values
    lows : sequence
        sequence of low values
    ticksize : int
        size of open and close ticks in points
    colorup : color
        the color of the lines where close >= open
    colordown : color
        the color of the lines where close <  open
    alpha : float
        bar transparency

    Returns
    -------
    ret : tuple
        (lineCollection, barCollection)
    """

    return candlestick2_ohlc(ax, opens, highs, lows, closes, width=width,
                     colorup=colorup, colordown=colordown,
                     alpha=alpha)


def candlestick2_ohlc(ax, opens, highs, lows, closes, width=4,
                 colorup='k', colordown='r',
                 alpha=0.75,
                 ):
    """Represent the open, close as a bar line and high low range as a
    vertical line.

    NOTE: this code assumes if any value open, low, high, close is
    missing they all are missing


    Parameters
    ----------
    ax : `Axes`
        an Axes instance to plot to
    opens : sequence
        sequence of opening values
    highs : sequence
        sequence of high values
    lows : sequence
        sequence of low values
    closes : sequence
        sequence of closing values
    ticksize : int
        size of open and close ticks in points
    colorup : color
        the color of the lines where close >= open
    colordown : color
        the color of the lines where close <  open
    alpha : float
        bar transparency

    Returns
    -------
    ret : tuple
        (lineCollection, barCollection)
    """

    _check_input(opens, highs, lows, closes)

    delta = width / 2.
    barVerts = [((i - delta, open),
                 (i - delta, close),
                 (i + delta, close),
                 (i + delta, open))
                for i, open, close in zip(range(len(opens)), opens, closes)
                if open != -1 and close != -1]

    rangeSegments = [((i, low), (i, high))
                     for i, low, high in zip(range(len(lows)), lows, highs)
                     if low != -1]

    colorup = mcolors.to_rgba(colorup, alpha)
    colordown = mcolors.to_rgba(colordown, alpha)
    colord = {True: colorup, False: colordown}
    colors = [colord[open < close]
              for open, close in zip(opens, closes)
              if open != -1 and close != -1]

    useAA = 0,  # use tuple here
    lw = 0.5,   # and here
    rangeCollection = LineCollection(rangeSegments,
                                     colors=colors,
                                     linewidths=lw,
                                     antialiaseds=useAA,
                                     )

    barCollection = PolyCollection(barVerts,
                                   facecolors=colors,
                                   edgecolors=colors,
                                   antialiaseds=useAA,
                                   linewidths=lw,
                                   )

    minx, maxx = 0, len(rangeSegments)
    miny = min([low for low in lows if low != -1])
    maxy = max([high for high in highs if high != -1])

    corners = (minx, miny), (maxx, maxy)
    ax.update_datalim(corners)
    ax.autoscale_view()

    # add these last
    ax.add_collection(rangeCollection)
    ax.add_collection(barCollection)
    return rangeCollection, barCollection


def volume_overlay(ax, opens, closes, volumes,
                   colorup='k', colordown='r',
                   width=4, alpha=1.0):
    """Add a volume overlay to the current axes.  The opens and closes
    are used to determine the color of the bar.  -1 is missing.  If a
    value is missing on one it must be missing on all

    Parameters
    ----------
    ax : `Axes`
        an Axes instance to plot to
    opens : sequence
        a sequence of opens
    closes : sequence
        a sequence of closes
    volumes : sequence
        a sequence of volumes
    width : int
        the bar width in points
    colorup : color
        the color of the lines where close >= open
    colordown : color
        the color of the lines where close <  open
    alpha : float
        bar transparency

    Returns
    -------
    ret : `barCollection`
        The `barrCollection` added to the axes

    """

    colorup = mcolors.to_rgba(colorup, alpha)
    colordown = mcolors.to_rgba(colordown, alpha)
    colord = {True: colorup, False: colordown}
    colors = [colord[open < close]
              for open, close in zip(opens, closes)
              if open != -1 and close != -1]

    delta = width / 2.
    bars = [((i - delta, 0), (i - delta, v), (i + delta, v), (i + delta, 0))
            for i, v in enumerate(volumes)
            if v != -1]

    barCollection = PolyCollection(bars,
                                   facecolors=colors,
                                   edgecolors=((0, 0, 0, 1), ),
                                   antialiaseds=(0,),
                                   linewidths=(0.5,),
                                   )

    ax.add_collection(barCollection)
    corners = (0, 0), (len(bars), max(volumes))
    ax.update_datalim(corners)
    ax.autoscale_view()

    # add these last
    return barCollection


def volume_overlay2(ax, closes, volumes,
                    colorup='k', colordown='r',
                    width=4, alpha=1.0):
    """
    Add a volume overlay to the current axes.  The closes are used to
    determine the color of the bar.  -1 is missing.  If a value is
    missing on one it must be missing on all

    nb: first point is not displayed - it is used only for choosing the
    right color


    Parameters
    ----------
    ax : `Axes`
        an Axes instance to plot to
    closes : sequence
        a sequence of closes
    volumes : sequence
        a sequence of volumes
    width : int
        the bar width in points
    colorup : color
        the color of the lines where close >= open
    colordown : color
        the color of the lines where close <  open
    alpha : float
        bar transparency

    Returns
    -------
    ret : `barCollection`
        The `barrCollection` added to the axes

    """

    return volume_overlay(ax, closes[:-1], closes[1:], volumes[1:],
                          colorup, colordown, width, alpha)


def volume_overlay3(ax, quotes,
                    colorup='k', colordown='r',
                    width=4, alpha=1.0):
    """Add a volume overlay to the current axes.  quotes is a list of (d,
    open, high, low, close, volume) and close-open is used to
    determine the color of the bar

    Parameters
    ----------
    ax : `Axes`
        an Axes instance to plot to
    quotes : sequence of (time, open, high, low, close, ...) sequences
        data to plot.  time must be in float date format - see date2num
    width : int
        the bar width in points
    colorup : color
        the color of the lines where close1 >= close0
    colordown : color
        the color of the lines where close1 <  close0
    alpha : float
         bar transparency

    Returns
    -------
    ret : `barCollection`
        The `barrCollection` added to the axes


    """

    colorup = mcolors.to_rgba(colorup, alpha)
    colordown = mcolors.to_rgba(colordown, alpha)
    colord = {True: colorup, False: colordown}

    dates, opens, highs, lows, closes, volumes = list(zip(*quotes))
    colors = [colord[close1 >= close0]
              for close0, close1 in zip(closes[:-1], closes[1:])
              if close0 != -1 and close1 != -1]
    colors.insert(0, colord[closes[0] >= opens[0]])

    right = width / 2.0
    left = -width / 2.0

    bars = [((left, 0), (left, volume), (right, volume), (right, 0))
            for d, open, high, low, close, volume in quotes]

    sx = ax.figure.dpi * (1.0 / 72.0)  # scale for points
    sy = ax.bbox.height / ax.viewLim.height

    barTransform = Affine2D().scale(sx, sy)

    dates = [d for d, open, high, low, close, volume in quotes]
    offsetsBars = [(d, 0) for d in dates]

    useAA = 0,  # use tuple here
    lw = 0.5,   # and here
    barCollection = PolyCollection(bars,
                                   facecolors=colors,
                                   edgecolors=((0, 0, 0, 1),),
                                   antialiaseds=useAA,
                                   linewidths=lw,
                                   offsets=offsetsBars,
                                   transOffset=ax.transData,
                                   )
    barCollection.set_transform(barTransform)

    minpy, maxx = (min(dates), max(dates))
    miny = 0
    maxy = max([volume for d, open, high, low, close, volume in quotes])
    corners = (minpy, miny), (maxx, maxy)
    ax.update_datalim(corners)
    #print 'datalim', ax.dataLim.bounds
    #print 'viewlim', ax.viewLim.bounds

    ax.add_collection(barCollection)
    ax.autoscale_view()

    return barCollection


def index_bar(ax, vals,
              facecolor='b', edgecolor='l',
              width=4, alpha=1.0, ):
    """Add a bar collection graph with height vals (-1 is missing).

    Parameters
    ----------
    ax : `Axes`
        an Axes instance to plot to
    vals : sequence
        a sequence of values
    facecolor : color
        the color of the bar face
    edgecolor : color
        the color of the bar edges
    width : int
        the bar width in points
    alpha : float
       bar transparency

    Returns
    -------
    ret : `barCollection`
        The `barrCollection` added to the axes

    """

    facecolors = (mcolors.to_rgba(facecolor, alpha),)
    edgecolors = (mcolors.to_rgba(edgecolor, alpha),)

    right = width / 2.0
    left = -width / 2.0

    bars = [((left, 0), (left, v), (right, v), (right, 0))
            for v in vals if v != -1]

    sx = ax.figure.dpi * (1.0 / 72.0)  # scale for points
    sy = ax.bbox.height / ax.viewLim.height

    barTransform = Affine2D().scale(sx, sy)

    offsetsBars = [(i, 0) for i, v in enumerate(vals) if v != -1]

    barCollection = PolyCollection(bars,
                                   facecolors=facecolors,
                                   edgecolors=edgecolors,
                                   antialiaseds=(0,),
                                   linewidths=(0.5,),
                                   offsets=offsetsBars,
                                   transOffset=ax.transData,
                                   )
    barCollection.set_transform(barTransform)

    minpy, maxx = (0, len(offsetsBars))
    miny = 0
    maxy = max([v for v in vals if v != -1])
    corners = (minpy, miny), (maxx, maxy)
    ax.update_datalim(corners)
    ax.autoscale_view()

    # add these last
    ax.add_collection(barCollection)
    return barCollection

         
if __name__ == '__main__':    
    
    date1 = datetime.datetime(2016, 12, 1)
    date2 = datetime.datetime(2016, 12, 19)
    data = DataCenter.get_intraday_data('AAPL', date1, date2, 'IntradayGoogle', 'daily')
#     dataDay = DataCenter.aggregate_intraday_data(data, datetime.timedelta(days=1))
# quotes = [[date2num(rec[0])]+rec[1:] for rec in data]
    quotes = data
    
    
    fig, ax = plt.subplots()
    fig.subplots_adjust(bottom=0.2)
    
#     _plot_ohlc_ax(ax, quotes)
#     _plot_volume_ax(ax, quotes)
    plot_price_volume(fig, quotes)

    plt.show()
