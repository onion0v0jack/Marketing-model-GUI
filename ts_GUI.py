# 版本號： ver 1.0
import datetime
import itertools
import os
import random
import sys
import warnings
import pandas as pd
from matplotlib.font_manager import FontProperties
from mplWidget import MplWidget
from pandasModel import pandasModel
from PySide2 import QtCore
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from statsmodels.tsa.arima_model import ARIMA
from thread import WorkThread

warnings.filterwarnings("ignore") # 要求忽略warning
import matplotlib.pyplot as plt
plt.style.use('ggplot')   # 設定畫圖風格為ggplot
plt.rcParams['font.sans-serif'] = ['SimHei'] # 設定相容中文 
plt.rcParams['axes.unicode_minus'] = False
pd.options.mode.chained_assignment = None

QtCore.QCoreApplication.addLibraryPath(os.path.join(os.path.dirname(QtCore.__file__), "plugins"))  # 掃plugin套件(windows必備)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # 設定持續使用的變數
        self.Data = None        # 輸入資料
        self.column_name = None # 輸入資料需要建立模型的變數名稱
        self.model = None       # 未訓練的模型，只有參數
        self.column_model_dict = None 
        self.worker = None
        self.model_fit = None   # 已訓練的模型
        self.result = None      # 訓練預測結果整理
        self.value_bar = 0
        self.p_range, self.d_range, self.q_range = range(0, 7), range(0, 3), range(0, 7)

        #【設定初始化，UI標題與視窗大小】
        self.setWindowTitle('Marketing model ver 1.0')
        self.setWindowIcon(QIcon("favicon.ico"))
        self.resize(QSize(1300, 950))

        #【設定UI中的元件】
        # 按鍵顯示
        self.btn_upload_csv = QPushButton('載入csv資料')
        self.btn_run_model = QPushButton('執行預測')
        self.btn_run_break = QPushButton('動作中斷')
        self.btn_download_result = QPushButton('下載預測結果')
        # 字元顯示
        self.label_maintitle = QLabel('銷售模型預測程式')
        self.label_upload_filename = QLabel()    # 如果一開始沒有要設定內容，可直接設定初始為空白
        self.label_input_data = QLabel('輸入資料')
        self.label_output_plot = QLabel('預測結果折線圖')
        self.label_output_data = QLabel('預測兩期結果') 
        self.label_current_message = QLabel('')
        # self.version_number = QLabel('V1.0')
        # 進度條顯示
        self.bar_upload = QProgressBar()
        # 表格顯示
        self.table_input_data = QTableView()
        self.table_output_data = QTableView()
        # 圖片顯示
        self.plot_output_result = MplWidget()
        ### 字型設定
        self.label_maintitle.setStyleSheet("QLabel{font-family: Microsoft JhengHei; color: rgb(0, 0, 0); font-size: 15pt; font-weight: bold;}")
        self.label_input_data.setStyleSheet("QLabel{font-family: Microsoft JhengHei; color: rgb(0, 0, 0); font-size: 12pt; font-weight: bold;}")
        self.label_output_plot.setStyleSheet("QLabel{font-family: Microsoft JhengHei; color: rgb(0, 0, 0); font-size: 12pt; font-weight: bold;}")
        self.label_output_data.setStyleSheet("QLabel{font-family: Microsoft JhengHei; color: rgb(0, 0, 0); font-size: 12pt; font-weight: bold;}")
        self.label_upload_filename.setStyleSheet("QLabel{font-family: Microsoft JhengHei; color: rgb(0, 0, 0); font-size: 9pt}")
        self.label_current_message.setStyleSheet("QLabel{font-family: Microsoft JhengHei; color: rgb(0, 0, 0); font-size: 10pt;}")
        self.label_upload_filename.setWordWrap(True) # 自動換行
        self.label_current_message.setWordWrap(True)
        ### 按鍵字元設定
        self.btn_upload_csv.setStyleSheet("QPushButton{font-family: Microsoft JhengHei;}")
        self.btn_run_model.setStyleSheet("QPushButton{font-family: Microsoft JhengHei;}")
        self.btn_run_break.setStyleSheet("QPushButton{font-family: Microsoft JhengHei;}")
        self.btn_download_result.setStyleSheet("QPushButton{font-family: Microsoft JhengHei;}")

        ### 進度條設定
        self.bar_upload.setRange(0, 4)
        self.bar_upload.setValue(0)
        self.bar_upload.setStyleSheet(
            """
            QProgressBar{
                font-family: Microsoft JhengHei; 
                background-color: rgb(255, 230, 204); 
                text-align: center;
                } 
            QProgressBar::chunk{
                background-color: rgb(230, 132, 0);
                }
            """
        )
        ### 表格大小設定
        self.table_input_data.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents) # 把顯示表格的寬調整到最小
        self.table_output_data.setMinimumHeight(105) # 設定顯示的最小高度
        self.table_output_data.setMaximumHeight(110) # 設定顯示的最大高度
        ### 圖片大小設定
        self.plot_output_result.setMinimumHeight(475)

        #【設定佈局(layout)】
        # main layout
        layout = QHBoxLayout() # 建立layout並指定layout為水平切分 # 建立layout之後要定義一個widget讓layout設定進去(註*1)
        
        # left layout
        left_layout = QVBoxLayout()                  # 設定此layout為垂直切分
        left_layout.addWidget(self.label_maintitle)  # 建立layout之後就可以塞元件了
        left_layout.addWidget(self.btn_upload_csv)
        left_layout.addWidget(self.bar_upload)
        left_layout.addWidget(self.label_upload_filename)
        left_layout.addWidget(self.label_input_data)
        left_layout.addWidget(self.table_input_data)
        left_widget = QWidget()
        left_widget.setLayout(left_layout)           # 建立left layout的widget(參考main layout的註*1)

        # right layout
        right_layout = QVBoxLayout() 
        right_layout.addWidget(self.label_output_plot)
        right_layout.addWidget(self.plot_output_result)
        right_layout.addWidget(self.label_output_data)
        right_layout.addWidget(self.table_output_data)
        # 在right layout裡面加入一個水平切分的子layout
        run_output_layout = QHBoxLayout()                  ###
        run_output_layout.addWidget(self.btn_run_model)
        run_output_layout.addWidget(self.btn_run_break)
        run_output_layout.addWidget(self.btn_download_result)
        run_output_widget = QWidget()
        run_output_widget.setLayout(run_output_layout)     # 子layout收尾成widget
        run_process_layout = QHBoxLayout()                 ###
        run_process_layout.addWidget(self.label_current_message)
        run_process_layout.addWidget(self.bar_upload)
        # run_process_layout.addWidget(self.version_number)
        run_process_layout.setStretchFactor(self.label_current_message, 3)
        run_process_layout.setStretchFactor(self.bar_upload, 2)  
        # run_process_layout.setStretchFactor(self.version_number, 1)  
        run_process_widget = QWidget()
        run_process_widget.setLayout(run_process_layout)     # 子layout收尾成widget
        right_layout.addWidget(run_output_widget)          # 在right_layout加入run_output_widget與run_process_widget
        right_layout.addWidget(run_process_widget)
            
        right_widget = QWidget()
        right_widget.setLayout(right_layout)               # 建立right layout的widget
        
        layout.addWidget(left_widget)                 # 設定好left與right layout的widget之後加入在main layout
        layout.addWidget(right_widget)
        layout.setStretchFactor(left_widget, 1)       # 設定left_widget與right_widget的比例
        layout.setStretchFactor(right_widget, 3) 
        main_widget = QWidget()                       # (註*1)每一次建layout後要用widget包
        main_widget.setLayout(layout)                 # (註*1)每一次建layout後要用widget包
        self.setCentralWidget(main_widget)            # 設定main_widget為中心視窗

        #【設定button觸發的slot(function)】
        self.btn_upload_csv.clicked.connect(self.upload_data_slot)
        self.btn_run_model.clicked.connect(self.run_model_slot)
        self.btn_run_break.clicked.connect(self.break_slot)
        self.btn_download_result.clicked.connect(self.download_data_slot)

        # 【設定thread】
        self.work = None
        self.stopped = None            # 暫停thread標籤

    def upload_data_slot(self):
        """Slot of uploading data (with btn_upload_csv)"""
        file, _ = QFileDialog.getOpenFileName(self, "Open file", "", "Data Files (*.csv)")  # 建立開啟檔案的對話盒(dialog)
        if file:
            print('file path: {}'.format(file))
            self.label_upload_filename.setText(file)                 # 將label_upload_filename複寫為檔名(file)
            self.Data = pd.read_table(r'{}'.format(file), sep = ',') # 寫入檔案
            self.table_input_data.setModel(pandasModel(self.Data))   # 在table_input_data顯示輸入資料的表格
 
    def run_model_slot(self):
        """Slot of running model (with btn_run_model)"""
        if self.Data is None:
            self.label_current_message.setText('尚未有資料以執行！請確認是否已載入資料。')
        else:
            self.stopped = False
            self.train_model1()
            self.btn_run_model.setEnabled(False)

    def break_slot(self):
        """Slot of stopping (with btn_run_break)"""
        if (self.Data is None) or (self.stopped != False):
            print('正常不反應')
            self.label_current_message.setText('')
        else:
            print('Thread stopped.')
            self.work.stopped = True
            self.bar_upload.reset()
            self.label_current_message.setText('程序中斷。')
            self.btn_run_model.setEnabled(True)
    
    def complete_slot(self, data):
        """Slot of stopping (with btn_run_break)"""
        # Show result
        self.result = data
        self.table_output_data.setModel(pandasModel(data.loc[:, ['date'] + [i for i in self.column_name]]))  # 顯示表格在table_output_data
        self.show_plot() # 參照show_plot()

        self.label_current_message.setText('模型計算完畢！')
        self.stopped = False
        self.btn_run_model.setEnabled(True)
        
    def download_data_slot(self):
        """Slot of downloading data (with btn_download_result)"""
        if self.result is None:
            self.label_current_message.setText('尚未有預測結果！請確認是否已載入資料並執行預測。')
        else:
            fileName, _ = QFileDialog.getSaveFileName(self, 'Save file', '', '*.csv')  # 建立儲存檔案的對話盒(dialog)
            if fileName:
                self.result['date'] = pd.to_datetime(self.result['date'])
                raw_input_data = self.Data.copy()  # 需要把原資料copy，否則直接取用的話，輸出結果會隨著下載次數而無謂增加
                output_data = raw_input_data.append(self.result.loc[:, ['date'] + [i for i in self.column_name]])
                output_data.to_csv(fileName, index = None)
    
    def train_model1(self):
        if self.Data.columns[0] != 'date':
            self.label_current_message.setText('請確認資料欄位名稱，第一個欄位為date，且格式為yyyy/mm/dd或yyyy-mm-dd')
        else :
            self.label_current_message.setText('模型計算中，請稍後...')
            self.Data.loc[:, 'date'] = pd.to_datetime(self.Data.loc[:, 'date'])
            self.Data = self.Data.sort_values('date')
            self.column_name = self.Data.columns[1:]
            # self.p_range, self.d_range, self.q_range = range(0, 4), range(0, 2), range(0, 4)###############
            pdq, self.column_model_dict = list(itertools.product(self.p_range, self.d_range, self.q_range)), {}
            self.value_bar = 0
            self.bar_upload.setValue(self.value_bar)

            # TODO: new threadl class.
            self.work = WorkThread(self.Data, self.column_name, pdq, self.model, self.model_fit)
            self.work.start()
            self.work.processbar_trigger.connect(self.set_processbar_value)
            self.work.result_trigger.connect(self.complete_slot)
    
    def set_processbar_value(self, value):
        self.bar_upload.setValue(value)

    def show_plot(self):
        """Slot of showing plot"""
        if self.result is None:
            print('目前無結果。')
        else:
            self.plot_output_result.setRows(len(self.column_name))  # 設定subplot的列數
            for i, column in enumerate(self.column_name): 
                self.plot_output_result.canvas.ax[i].plot(          # 畫原資料 + 預測結果，以紅色線表示
                    range(1, len(self.Data) + 3),
                    [i for i in self.Data.loc[:, column]] + [i for i in self.result.loc[:, column]], 
                    linewidth = 1, color = 'firebrick'
                    )
                self.plot_output_result.canvas.ax[i].plot(          # 畫原資料，以藍色線表示(使得只有預測曲線是紅的)
                    range(1, len(self.Data) + 1), self.Data.loc[:, column], color = 'steelblue'
                    )
                self.plot_output_result.canvas.ax[i].fill_between(  # 畫信賴區間的背景
                    range(len(self.Data), len(self.Data) + 3), 
                    [self.Data.loc[:, column].values[-1]] + [i for i in self.result.loc[:, column + '_LB']], 
                    [self.Data.loc[:, column].values[-1]] + [i for i in self.result.loc[:, column + '_UB']], 
                    facecolor = 'salmon', alpha = 0.6, interpolate = True
                )
                self.plot_output_result.canvas.ax[i].set_ylabel(column)
            self.plot_output_result.canvas.ax[-1].set_xlabel('Week', fontproperties = FontProperties(fname = "SimHei.ttf", size = 14))
            self.plot_output_result.canvas.figure.subplots_adjust(wspace = 0.1, hspace = 0.5) # 調整子圖間距
            self.plot_output_result.canvas.draw()  # 類似plt.show()

def main():
    app = QApplication([])
    app.setStyle(QStyleFactory.create('fusion'))
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()