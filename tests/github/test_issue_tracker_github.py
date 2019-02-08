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


GH_TOKENS = ['bb937fbe4a0e04ec092aa92c355d8754996bf39b',
             'b687bec66f9e7fc09ab19d24076da6c584c60fe1',
             '9d512e3cd8fe98e210dd46e8f8da973cc5a1b025',
             '04ef01bcaee67991465dfec00211cd133579be69',
             '3b85828f65e962502da2f2b236f759c557e1419c']


def test(g):
    g.init_db("db_2048")
    g.create_project("db_2048", "2048")
    g.import_git_data("db_2048", "2048", "repo_2048", "C:\\Users\\atlanmod\\Desktop\\2048")
    g.import_github_issue_data("db_2048", "2048", "repo_2048", "2048-tracker", "gabrielecirulli/2048", GH_TOKENS)


def main():
    g = Gitana(CONFIG)
    g.delete_previous_logs()

    print "starting .."
    test(g)


if __name__ == "__main__":
    main()
