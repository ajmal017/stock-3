'''
Created on Dec. 24, 2017

@author: Wei.Wang
'''

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

import os, sys, csv
from datetime import date, datetime, timedelta, time
import time as pythontime
from dataCenter import DataCenter, dataSources, plotTypes, intervals
from plotUtils import plot_price_volume
# from dateutil.parser import parse
# import sys, re, subprocess
import sqlite3, re, os 

# # matplotlib.use('QtAgg')
# # matplotlib.rcParams['backend.qt5']='PyQt'
# from matplotlib.figure import Figure
# from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
# # from matplotlib.backends.backend_pdf import PdfPages
# import matplotlib.pyplot as plt 

# from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
# from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
    
class PlotFrame(QFrame):
    """Schedule frame"""
    def __init__(self, parent = None):
        super(PlotFrame, self).__init__()
        self.mainFrame = parent
        self.controlPanel = self.mainFrame.controlPanel
        
        self.setLayout(QVBoxLayout())
        
        ##: Plot parameters
        self.dpi = 72          
        self.fontsize = 14
        self.textfontsize = 14
        self.linewidth = 3
        
        
        # a figure instance to plot on
        self.fig = plt.figure()

        # this is the Canvas Widget that displays the `figure`
        # it takes the `figure` instance as a parameter to __init__
        self.canvas = FigureCanvas(self.fig)

        # this is the Navigation widget
        # it takes the Canvas widget and a parent
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        self.layout().addWidget(self.toolbar)
        self.layout().addWidget(self.canvas)
    
        self.plot()
        

    def get_data(self):
        """
           Generate attendance data for the plot.
           Attendance is defined as the maximum number of people presented in a given period of time. 
        """
        
        symbol, dataSource, startDatetime, endDatetime, plotType, interval = self.controlPanel.get_parameters()
        data = DataCenter.get_intraday_data(symbol, startDatetime, endDatetime, dataSource, interval)
        return data
    
        
    def plot(self):
        
        QApplication.setOverrideCursor(Qt.WaitCursor)
        data = self.get_data()
        QApplication.restoreOverrideCursor()
        
        if not self.mainFrame.chkPopout.isChecked():
            self.fig.clf()
            plot_price_volume(self.fig, data)
            self.canvas.draw()
        else:
            symbol = self.controlPanel.get_symbol()
            dlgFig = FigureDialog(data, plot_price_volume, symbol)
#             dlgFig.exec_()

            dlgFig.setWindowFlags(Qt.Window)
            dlgFig.show()
# 
#             fig = plt.figure()            
#             plot_price_volume(fig, data)
#             fig.show()
        
#         QApplication.restoreOverrideCursor()
        
        
#         plt.show()
#         
#         plotType = 'Line'
#         if plotType=='Line':
#             ##: Plot curve for minute
#             axes.plot(x, y, linewidth = 1)
#             axes.grid(True)
#         elif plotType=='Line':
#             ##: Plot bar for hours
#             axes.bar(x, y, align='edge', color='red', linewidth = self.linewidth, width=-.8)
#             axes.set_xticks(xticks)
#             axes.set_xticklabels(xticklabels, size=self.fontsize)
#             self.fig.gca().set_xlim(left=0)
# 
#         axes.set_ylabel('Attendance', size=self.fontsize)
#         axes.set_xlabel('Time', size=self.fontsize)
#         
#         self.canvas.draw()   
        
#         
#     def zoom_fun(self, event):
#         """Zoom in/out by scrolling mouse wheel."""
#         
#         # get the current x and y limits
#         base_scale = 1.5
#         ax = self.fig.axes[0]
#         cur_xlim = ax.get_xlim()
#         cur_ylim = ax.get_ylim()
#         cur_xrange = (cur_xlim[1] - cur_xlim[0])*.5
#         cur_yrange = (cur_ylim[1] - cur_ylim[0])*.5
#         xdata = event.xdata # get event x location
#         ydata = event.ydata # get event y location
#         if event.button == 'up':
#             # deal with zoom in
#             scale_factor = 1/base_scale
#         elif event.button == 'down':
#             # deal with zoom out
#             scale_factor = base_scale
#         else:
#             # deal with something that should never happen
#             scale_factor = 1
#             print event.button
#         # set new limits
#         ax.set_xlim([xdata - cur_xrange*scale_factor,
#                      xdata + cur_xrange*scale_factor])
#         ax.set_ylim([ydata - cur_yrange*scale_factor,
#                      ydata + cur_yrange*scale_factor])
#         #ax.grid(True)
#         self.canvas.draw()

class FigureDialog(QDialog):
    def __init__(self, data, plotFunc, symbol=''):
        super(FigureDialog, self).__init__()
        self.setLayout(QVBoxLayout())
        self.fig = plt.figure()
        self.setWindowTitle(symbol)
        self.setModal(False)
        # this is the Canvas Widget that displays the `figure`
        # it takes the `figure` instance as a parameter to __init__
        self.canvas = FigureCanvas(self.fig)

        # this is the Navigation widget
        # it takes the Canvas widget and a parent
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        self.layout().addWidget(self.toolbar)
        self.layout().addWidget(self.canvas)
    
        plotFunc(self.fig, data)
        self.canvas.draw()        
        
class ControlPanel(QGroupBox):
    def __init__(self, parent = None):
        super(ControlPanel, self).__init__()
        self.mainFrame = parent
        self.setTitle('Control Panel')
        
        self.setLayout(QVBoxLayout())
        
        frmSymbol = QFrame()
        frmSymbol.setLayout(QHBoxLayout())    
        self.txtSymbol = QLineEdit()
        frmSymbol.layout().addWidget(QLabel('Symbol:'))
        frmSymbol.layout().addWidget(self.txtSymbol)
        
        frmRange = QFrame()
        frmRange.setLayout(QHBoxLayout())    
        self.txtFrom = QDateEdit()
        self.txtFrom.setCalendarPopup(True)
        self.txtFrom.setDisplayFormat('MM/dd/yyyy')
        self.txtFrom.setDate(date.today())
        self.txtTo = QDateEdit()
        self.txtTo.setCalendarPopup(True)
        self.txtTo.setDisplayFormat('MM/dd/yyyy')   
        self.txtTo.setDate(date.today())
#         self.txtFrom.dateChanged.connect(self.plot)
#         self.txtTo.dateChanged.connect(self.plot)
#         self.txtFrom.setDisabled(True)
#         self.txtTo.setDisabled(True)
#         self.txtFrom.dateChanged.connect(self.plot)
#         self.txtTo.dateChanged.connect(self.plot)
        frmRange.layout().addWidget(QLabel('From:'))         
        frmRange.layout().addWidget(self.txtFrom)
        frmRange.layout().addWidget(QLabel('To:'))
        frmRange.layout().addWidget(self.txtTo)
        
        frmDataSource = QFrame()
        frmDataSource.setLayout(QHBoxLayout())
        self.dataSources = dataSources
        self.comboDataSource = QComboBox()
        self.comboDataSource.addItems(self.dataSources)
        frmDataSource.layout().addWidget(QLabel('Data Source:'))    
        frmDataSource.layout().addWidget(self.comboDataSource)    
        
        frmPlotType = QFrame()
        frmPlotType.setLayout(QHBoxLayout())
        self.comboPlotType = QComboBox()
        self.plotTypes = plotTypes
        self.comboPlotType.addItems(self.plotTypes)
        frmPlotType.layout().addWidget(QLabel('Plot Type:'))    
        frmPlotType.layout().addWidget(self.comboPlotType)    
        
        frmInterval = QFrame()
        frmInterval.setLayout(QHBoxLayout())
        self.comboInterval = QComboBox()
        self.intervals = intervals ##: ['1 min', 'hourly', 'daily', '5 min','15 min','30 min', '5 hour', 'monthly', 'yearly']
        self.comboInterval.addItems(self.intervals)
#         self.comboInterval.currentIndexChanged.connect(self.plot)
        frmInterval.layout().addWidget(QLabel('Interval'))
        frmInterval.layout().addWidget(self.comboInterval)
        
        self.layout().addWidget(frmSymbol)
        self.layout().addWidget(frmDataSource)
        self.layout().addWidget(frmPlotType)
        self.layout().addWidget(frmRange)
        self.layout().addWidget(frmInterval)

        ##: Temporal input when debug
        self.txtSymbol.setText('TSS')
        self.txtFrom.setDateTime(datetime(2015, 11, 10))
        self.txtTo.setDateTime(datetime(2015, 11, 17))
#         self.comboDataSource.setCurrentText('TickDataNetFonds')
        self.comboDataSource.setCurrentText('IntradayGoogle')
        self.comboPlotType.setCurrentText('Line')
        self.comboInterval.setCurrentIndex(2)
    
        self.comboInterval.currentIndexChanged.connect(self.plot)
        self.txtFrom.dateChanged.connect(self.plot)
        self.txtTo.dateChanged.connect(self.plot)
        
    def plot(self):
        self.mainFrame.frmPlot.plot()
    
    def get_time_range(self):
        timeStart = datetime.combine(self.txtFrom.date().toPyDate(), time.min)
        timeEnd = datetime.combine(self.txtTo.date().toPyDate(), time.max)
        return (timeStart, timeEnd)    
    
    def get_interval(self):    
        interval = self.comboInterval.currentText()
        return interval
    
    def get_symbol(self):
        return self.txtSymbol.text()
    
    def get_parameters(self):
        symbol = self.txtSymbol.text()
        startDatetime = datetime.combine(self.txtFrom.date().toPyDate(), time.min)
        endDatetime = datetime.combine(self.txtTo.date().toPyDate(), time.max)
        dataSource = self.comboDataSource.currentText()
        plotType = self.comboPlotType.currentText()
        interval = self.comboInterval.currentText()

        return (symbol, dataSource, startDatetime, endDatetime, plotType, interval)
    
class MainFrame(QFrame):
    """Employee frame"""
    def __init__(self, parent = None):
        super(MainFrame, self).__init__()
        self.mainWindow = parent
        
        self.setLayout(QHBoxLayout())
        
        frmControls = QGroupBox('Controls')
        frmControls.setLayout(QVBoxLayout())
        self.controlPanel = ControlPanel(self)
        
        frmButton = QFrame()
        btnPlot = QPushButton('Plot')
        btnPlot.clicked.connect(self.on_btnPlot_clicked)
        self.chkPopout = QCheckBox('Pop out')
        frmButton.setLayout(QHBoxLayout())
        frmButton.layout().addWidget(btnPlot)
        frmButton.layout().addWidget(self.chkPopout)
        
        frmControls.layout().addWidget(self.controlPanel)
        frmControls.layout().addWidget(frmButton)
        frmControls.layout().addWidget(QLabel(''))
        frmControls.layout().setStretch(2,100)
        
        self.frmPlot = PlotFrame(self)
        
        self.layout().addWidget(self.frmPlot)
        self.layout().addWidget(frmControls)
        self.layout().setStretch(0, 100)

    def on_btnPlot_clicked(self):
        self.frmPlot.plot()    
    
        
class MainWindow(QMainWindow):
    """This class is for the system main window"""
    def __init__(self, parent = None):
        super(MainWindow, self).__init__(parent)
        self.mainFrame = MainFrame()
            
        self.setCentralWidget(self.mainFrame)   
        
        self.setWindowTitle("Millionaire Project")
        self.showMaximized() 
#         self.resize(1200, 800)    

        ####################################################
        ##: Create File Menu        
        self.file_menu = self.menuBar().addMenu("File")
        
        self.file_load_action = QAction("Load in...", self)
#         self.login_action.setShortcut("Ctrl+L")
#         self.login_action.triggered.connect(self.on_login_clicked)
        self.file_menu.addAction(self.file_load_action)    
        
        self.file_exit_action = QAction("Exit", self)
        self.file_exit_action.triggered.connect(self.close)
        self.file_menu.addAction(self.file_exit_action)    
        
        ##: Create Data Menu        
        self.data_menu = self.menuBar().addMenu("Data")
        self.data_action = QAction("Validation", self)
#         self.help_action.triggered.connect(self.showContents)
        self.about_action = QAction("About", self)
#         self.about_action.triggered.connect(self.showAbout)
        self.data_menu.addAction(self.data_action)        
        self.data_menu.addAction(self.about_action)    
        
        self.statusBar().showMessage("")    
                    
         
if __name__ == '__main__':    
#     pydoc -w fec > fec.html
#     create_database_raw_data()
    # start gui
    app = QApplication(sys.argv)

    main_window = MainWindow()
    main_window.show()
    
        
    sys.exit(app.exec_())
    