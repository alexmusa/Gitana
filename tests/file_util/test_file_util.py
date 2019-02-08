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


def _file_util_test():
    g = Gitana(CONFIG)
    g.delete_previous_logs()
    h = g.get_file_history("db_2048", "repo_2048", "readme.md", "origin/master", reversed=False, before_date="2014-03-19")
    v = g.get_file_version("db_2048", "repo_2048", "readme.md", "origin/master")

    print "here"


def main():
    _file_util_test()

if __name__ == "__main__":
    main()