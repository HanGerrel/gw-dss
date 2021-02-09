import sqlite3
from datetime import datetime


class DbApi:
    connect = None

    @staticmethod
    def connect(db_path):
        print(db_path)
        DbApi.connect = sqlite3.connect(db_path)

    @staticmethod
    def get_cursor():
        return DbApi.connect.cursor()

    @staticmethod
    def close():
        DbApi.connect.close()

    @staticmethod
    def add_new_call(_date, _phone_number, _talk_time, _call_status):
        query = f"""
                insert into Call_table(date, phone_number, talk_time, call_status)
                values ({_date}, {_phone_number}, {_talk_time}, {_call_status})
        """

        DbApi.get_cursor().execute(query)

    @staticmethod
    def get_calls_info_by_date(_date_start, _date_end):
        """_date_* - datetime object"""
        cursor = DbApi.get_cursor()
        date_start = _date_start.strftime('%Y-%m-%d')
        date_end = _date_end.strftime('%Y-%m-%d')
        # strftime - первый день недели - воскресенье
        query = f"""
                    select strftime('%w', date) WeekNumber,
                    strftime('%H', date) HourNumber,
                    count(id)/(
                        select DISTINCT
                        cast((strftime('%d', '{date_end}') - strftime('%d', '{date_start}') + 1.0)/7.0 as int) * 1.
                        from Call_table
                    )
                    from Call_table
                    where (date BETWEEN '{date_start}' AND '{date_end}')
                    group by WeekNumber, HourNumber
                    """

        cursor.execute(query)
        return cursor.fetchall()

    @staticmethod
    def get_first_date():
        cursor = DbApi.get_cursor()
        query = f"""
            select date
            from Call_table
            order by id limit 1
        """

        cursor.execute(query)
        return datetime.strptime(cursor.fetchall()[0][0], '%Y-%m-%d %H:%M:%S')
