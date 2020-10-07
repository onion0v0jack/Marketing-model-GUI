import datetime
import numpy as np
import pandas as pd

from PySide2.QtCore import *
from PySide2.QtWidgets import *
from PySide2.QtGui import *
from statsmodels.tsa.arima_model import ARIMA

class WorkThread(QThread):
    processbar_trigger = Signal(int)
    result_trigger = Signal(pd.DataFrame)

    def __init__(self, data, column_name, pdq, model, model_fit):
        super().__init__()

        self.data = data
        self.column_name = column_name
        self.pdq = pdq
        self.model = model
        self.model_fit = model_fit
        self.column_model_dict = {}
        self.column_rmse_dict = {}
        self.result = None
        self.stopped = False

    def run(self):
        # # 【遍歷模型，尋找個別適合的參數】
        for i, column in enumerate(self.column_name):
            min_criteria_value, min_criteria_param = 0, 0
            print('開始建立{}的模型'.format(column))
            for param in self.pdq:
                self.model = None
                if self.stopped == True:
                    print('Thread stopped.')
                    return
                try:
                    self.model = ARIMA(self.data.loc[:, column], order = param)
                    self.model_fit = self.model.fit(disp = 0)
                    # criteria_value = self.model_fit.aic    #aic
                    criteria_value = np.sqrt((self.model_fit.resid.values**2).mean()) #rmse
                    if (min_criteria_value == 0) or (min_criteria_value > criteria_value):
                        min_criteria_value, min_criteria_param = criteria_value, param
                except:
                    pass
                # else:
                #     print('{}: OK'.format(param))
            self.column_model_dict[column] = min_criteria_param
            self.column_rmse_dict[column] = min_criteria_value

            # TODO: Emit signal to modify the value of process bar.(emit:發射信號)
            self.processbar_trigger.emit(i + 1)

        print('最後確定模型pdq: {}'.format(self.column_model_dict))
        print('模型rmse: {}'.format(self.column_rmse_dict))
        # # 【確定參數之後正式建模預測】
        # 建立結果的表格
        last_date = self.data.loc[:, 'date'].values[-1]  
        next1_date, next2_date = pd.to_datetime(last_date) + datetime.timedelta(days = 7), pd.to_datetime(last_date) + datetime.timedelta(days = 14)
        self.result = pd.DataFrame({'date': [next1_date.strftime('%Y-%m-%d'), next2_date.strftime('%Y-%m-%d')]})
        # 確定參數後個別run時序模型
        for column in self.column_name:
            self.model = None
            self.model = ARIMA(self.data.loc[:, column], order = self.column_model_dict[column])
            self.model_fit = self.model.fit(disp = 0)

            self.result.loc[:, column] = [round(value, 3)for value in self.model_fit.forecast(2)[0]]                # 預測值
            self.result.loc[:, column + '_LB'] = [round(CI[0], 3) for CI in self.model_fit.forecast(2)[-1]]         # 預測下界
            self.result.loc[:, column + '_UB'] = [round(CI[1], 3) for CI in self.model_fit.forecast(2)[-1]]         # 預測上界
        
        # TODO: Emit signal to return result(pd.DataFrame)
        self.result_trigger.emit(self.result)
    
            
