from PySide2.QtGui import *
import matplotlib.pyplot as plt
from PySide2.QtCore import *
from PySide2.QtWidgets import *
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import (
        FigureCanvas, NavigationToolbar2QT as NavigationToolbar)

plt.style.use('ggplot')

class MplWidget(QWidget):
    
    def __init__(self, parent = None):
        self.plt_rows = None
        
        QWidget.__init__(self, parent)
        
        self.canvas = FigureCanvas(Figure())
        
        vertical_layout = QVBoxLayout()
        vertical_layout.addWidget(self.canvas)
        vertical_layout.addWidget(NavigationToolbar(self.canvas, self))
        
        self.setLayout(vertical_layout)

    def setRows(self, row):
        self.canvas.figure.clf()
        self.canvas.ax = self.canvas.figure.subplots(
            row, 1, sharex=True, subplot_kw = {'facecolor':'#EEEEEE'})  