import sqlite3
from datetime import date
from functools import partial

from PySide6.QtCore import QDate, QTranslator
from PySide6.QtWidgets import QTableWidgetItem, QFileDialog, QInputDialog, QErrorMessage, QMessageBox, QPushButton, \
    QApplication
from dateutil import relativedelta

from database.db_api import DbApi
from dataprocessing.input_data import InputData
from easysettings import EasySettings
from predict.predict import Predict


class ButtonHandler:
    class ErrorDialog(QMessageBox):
        def __init__(self, obj, e):
            super().__init__()
            self.setIcon(QMessageBox.Critical)
            self.setWindowTitle('ERROR')
            self.setText(str(e))
            btn1 = QPushButton('Выбрать новый путь к бд')
            btn1.clicked.connect(partial(ButtonHandler.set_db_path_triggered, obj))
            self.addButton(btn1, QMessageBox.AcceptRole)
            btn2 = QPushButton('Закрыть программу')
            btn2.clicked.connect(obj.close)
            self.addButton(btn2, QMessageBox.RejectRole)
            self.exec()

    @staticmethod
    def all_time_pressed(obj):
        try:
            obj.ui.date_start.setDate(QDate(DbApi.get_first_date()))
        except sqlite3.Error as e:
            ButtonHandler.ErrorDialog(obj, e)

    @staticmethod
    def last_year_pressed(ui):
        now = date.today()
        ui.date_start.setDate(QDate(now + relativedelta.relativedelta(years=-1)))

    @staticmethod
    def last_6_month_pressed(ui):
        now = date.today()
        ui.date_start.setDate(QDate(now + relativedelta.relativedelta(months=-6)))

    @staticmethod
    def last_3_month_pressed(ui):
        now = date.today()
        ui.date_start.setDate(QDate(now + relativedelta.relativedelta(months=-3)))

    @staticmethod
    def last_month_pressed(ui):
        now = date.today()
        ui.date_start.setDate(QDate(now + relativedelta.relativedelta(months=-1)))

    @staticmethod
    def analyze_pressed(obj):
        ui = obj.ui
        settings = EasySettings(".conf")
        cost = settings.get('channel_cost', 0)
        if not cost:
            ButtonHandler.set_hourly_payment_triggered(obj)
        predict_tables = [
            ui.predict_table_1,
            ui.predict_table_2,
            ui.predict_table_3,
            ui.predict_table_4,
            ui.predict_table_5,
            ui.predict_table_6,
            ui.predict_table_7
        ]
        cost_tables = [
            ui.cost_table_1,
            ui.cost_table_2,
            ui.cost_table_3,
            ui.cost_table_4,
            ui.cost_table_5,
            ui.cost_table_6,
            ui.cost_table_7
        ]
        date_start = ui.date_start.date().toPython()
        date_end = ui.date_end.date().toPython()
        try:
            lambda_by_shift = InputData.get_count_of_calls_by_range(date_start, date_end)
            if all(value == 0 for list_ in lambda_by_shift for value in list_):
                raise Exception('Empty data set')
            for i in range(len(lambda_by_shift)):
                table = predict_tables[i]
                cost_table = cost_tables[i]
                for j in range(len(lambda_by_shift[i])):
                    index = 1
                    predicts = Predict(range(1, 20), 20, lambda_by_shift[i][j], 12).get_predict()
                    for predict in predicts:
                        for characteristic in predict:
                            table.setItem(index, j + 2, QTableWidgetItem(characteristic))
                            index += 1

                        channel_cost = float(predict[0]) * cost
                        request_cost = (float(predict[0]) * cost) / float(predict[1])
                        request_cost = round(request_cost, 2)
                        cost_table.setItem(index - 3, j + 2, QTableWidgetItem(str(channel_cost)))
                        cost_table.setItem(index - 2, j + 2, QTableWidgetItem(str(request_cost)))
        except sqlite3.Error as e:
            ButtonHandler.ErrorDialog(obj, e)
        except Exception as e:
            QErrorMessage(obj).showMessage(str(e))

    @staticmethod
    def set_db_path_triggered(obj):
        db_path = QFileDialog.getOpenFileName(obj, 'Choose path to db')[0]
        if db_path:
            if DbApi.conn:
                DbApi.close()
            DbApi.connect(db_path)
            settings = EasySettings(".conf")
            settings.set('db_path', db_path)
            settings.save()

    @staticmethod
    def set_hourly_payment_triggered(obj):
        cost, ok = QInputDialog.getDouble(obj, 'Стоимость в час', 'Введите стоимость часа работы персонала')
        if ok:
            settings = EasySettings(".conf")
            settings.set('channel_cost', cost)
            settings.save()

    @staticmethod
    def switch_lang(obj, lang):
        translator = QTranslator()
        translator.load(f"gw-dss_{lang}", "./interface/translation/")

        if not QApplication.installTranslator(translator):
            msg = QErrorMessage(obj)
            msg.setWindowTitle('Error')
            msg.showMessage('Unable to install language')
        else:
            obj.ui.retranslateUi(obj)

            settings = EasySettings(".conf")
            settings.set('lang', lang)
            settings.save()
