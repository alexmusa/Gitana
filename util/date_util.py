#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

import calendar
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class DateUtil():
    """
    This class provides date utilities
    """

    def get_month_from_int(self, month_int):
        """
        converts int to month name

        :type month_int: int
        :param month_int: numeric representation of the month
        """
        return calendar.month_name[month_int]

    def get_weekday_from_int(self, day_int):
        """
        converts int to week day

        :type day_int: int
        :param day_int: numeric representation of the week day
        """
        return calendar.day_name[day_int]

    def get_start_time_span(self, reference_time, time_unit, format):
        """
        gets start time

        :type reference_time: datetime
        :param reference_time: input time

        :type time_unit: str
        :param time_unit: time unit (week, month, year)

        :type format: str
        :param format: time format (e.g, YYYY-mm-dd)
        """
        start_time = None
        if time_unit == "week":
            start_time = reference_time - timedelta(days=reference_time.weekday())
        elif time_unit == "month":
            start_time = reference_time - timedelta(days=reference_time.day - 1)
        elif time_unit == "year":
            start_time = reference_time - timedelta(days=reference_time.timetuple().tm_yday - 1)

        if start_time:
            start_time = start_time.strftime(format)

        return start_time

    def get_timestamp(self, creation_time, format):
        """
        gets timestamp from string

        :type creation_time: str
        :param creation_time: creation time

        :type format: str
        :param format: time format (e.g, YYYY-mm-dd)
        """
        return datetime.strptime(str(creation_time), format)

    def check_format_timestamp(self, s, format):
        """
        checks that a string respects a given date format

        :type s: str
        :param s: a string representation of a time

        :type format: str
        :param format: time format (e.g, YYYY-mm-dd)
        """
        flag = True
        try:
            self.get_datetime_from_string(s, format())
        except:
            flag = False

        return flag

    def get_datetime_from_string(self, target_time, format):
        """
        gets datetime Object from string

        :type target_time: str
        :param target_time: creation time

        :type format: str
        :param format: datetime format (e.g, YYYY-mm-dd)
        """
        try:
            time = datetime.strptime(str(target_time), format)
        except:
            time = None

        return time

    def get_string_from_datetime(self, target_time, format):
        """
        gets string from datetime Object

        :type target_time: datetime Object
        :param target_time: creation time

        :type format: str
        :param format: datetime format (e.g, YYYY-mm-dd)
        """
        try:
            time = target_time.strftime(format)
        except:
            time = None

        return time

    def increment_date(self, target_time, unit=None, increment=None):
        """
        increments a datetime Object with a given amount of time

        :type target_time: datetime Object
        :param target_time: target time to increment

        :type unit: str
        :param unit: unit of time (year, month, week, day). Default one is month

        :type increment: int
        :param increment: amount of time. By default is 3
        """
        if unit:
            digested = unit.lower()
        else:
            digested = "month"

        if not increment:
            increment = 3

        if digested == "year":
            incremented_target = target_time + relativedelta(years=increment)
        elif digested == "week":
            incremented_target = target_time + relativedelta(weeks=increment)
        elif digested == "day":
            incremented_target = target_time + relativedelta(days=increment)
        else:
            incremented_target = target_time + relativedelta(months=increment)

        return incremented_target

    def get_time_fromtimestamp(self, creation_time, format):
        """
        gets time Object from string

        :type creation_time: str
        :param creation_time: creation time

        :type format: str
        :param format: time format (e.g, YYYY-mm-dd)
        """
        try:
            time = datetime.fromtimestamp(creation_time).strftime(format)
        except:
            time = None

        return time