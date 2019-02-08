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

REFERENCES = ["master"]


def test_1():
    g = Gitana(CONFIG, None)
    g.delete_previous_logs()
    g.init_db("db_2048")
    g.create_project("db_2048", "2048")
    print "import git data"
    g.import_git_data("db_2048", "2048", "repo_2048", "C:\\Users\\atlanmod\\Desktop\\oss\\ants-work\\github-repos\\2048")
    print "import code function data"
    g.import_function_data("db_2048", "2048", "repo_2048", "C:\\Users\\atlanmod\\Desktop\\oss\\ants-work\\github-repos\\2048")


def test_2():
    g = Gitana(CONFIG, None)
    g.delete_previous_logs()
    g.init_db("db_2048")
    g.create_project("db_2048", "2048")
    print "import git data"
    g.import_git_data("db_2048", "2048", "repo_2048", "C:\\Users\\atlanmod\\Desktop\\oss\\ants-work\\github-repos\\2048")
    print "import code function data"
    g.import_function_data("db_2048", "2048", "repo_2048", "C:\\Users\\atlanmod\\Desktop\\oss\\ants-work\\github-repos\\2048")
    g.delete_function_data("db_2048", "2048", "repo_2048", ["origin/gh-pages"])
    g.delete_function_data("db_2048", "2048", "repo_2048", ["origin/master"])
    #g.delete_function_data("db_2048", "2048", "repo_2048", ["origin/master", "origin/gh-pages"])


def test_3():
    g = Gitana(CONFIG, None)
    g.delete_previous_logs()
    g.init_db("db_2048")
    g.create_project("db_2048", "2048")
    print "import git data"
    g.import_git_data("db_2048", "2048", "repo_2048", "C:\\Users\\atlanmod\\Desktop\\oss\\ants-work\\github-repos\\2048")
    print "import code function data"
    g.import_function_data("db_2048", "2048", "repo_2048", "C:\\Users\\atlanmod\\Desktop\\oss\\ants-work\\github-repos\\2048")
    g.delete_function_data("db_2048", "2048", "repo_2048", ["origin/master", "origin/gh-pages"])


def main():
    test_1()
    test_2()
    test_3()

if __name__ == "__main__":
    main()
