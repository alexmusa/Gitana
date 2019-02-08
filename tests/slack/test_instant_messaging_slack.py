#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

from gitana.gitana import Gitana

CONFIG = {
            'user': 'root',
            'password': 'root',
            'host': 'localhost',
            'port': '3306',
            'raise_on_warnings': False,
            'buffered': True
        }

SLACK_TOKENS = ['xoxp-67182691220-67204318994-110578093616-af58ccb5a30cb97455d256ee9acc0efc']


def test_1():
    g = Gitana(CONFIG)
    g.delete_previous_logs()
    g.init_db("bootstrap_db_test")
    g.create_project("bootstrap_db_test", "bootstrap")
    g.import_slack_data("bootstrap_db_test", "bootstrap", "slack_bootstrap", SLACK_TOKENS,
                        before_date="2016-08-12", channels=["random", "metascience", "softwareanalysis"])


def test_2():
    g = Gitana(CONFIG)
    g.delete_previous_logs()

    g.update_slack_data("bootstrap_db_test", "bootstrap", "slack_bootstrap", SLACK_TOKENS)


def main():
    print "starting 1.."
    test_1()
    print "starting 2.."
    test_2()

if __name__ == "__main__":
    main()
