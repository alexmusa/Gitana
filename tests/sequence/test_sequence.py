#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

from gitana.gitana import Gitana
from github import Github

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


def _papyrus():
    g = Gitana(CONFIG, None)
    g.delete_previous_logs()
    g.init_db("db_papyrus")
    g.create_project("db_papyrus", "papyrus")
    print "import git data"
    g.import_git_data("db_papyrus", "papyrus", "papyrus_repo", "C:\\Users\\atlanmod\\Desktop\\eclipse-git-projects\\papyrus", None, 1, None, 20)
    print "import bugzilla data"
    g.import_bugzilla_issue_data("_papyrus_db", "papyrus", "papyrus_repo", "bugzilla-papyrus", "https://bugs.eclipse.org/bugs/xmlrpc.cgi", "papyrus", None, 10)
    print "import eclipse forum data"
    g.import_eclipse_forum_data("_papyrus_db", "papyrus", "papyrus-eclipse", "https://www.eclipse.org/forums/index.php/f/121/", None, 4)
    print "import stackoverflow data"
    g.import_stackoverflow_data("_papyrus_db", "papyrus", "papyrus-stackoverflow", "papyrus", None, ['IFco1Gh5EJ*U)ZY5)16ZKQ(('])
    print "import code function data"
    g.import_code_data("db_papyrus", "papyrus", "papyrus_repo", "C:\\Users\\atlanmod\\Desktop\\eclipse-git-projects\\papyrus", 2, None, 20)


def _cesiumjs():

    TARGETS = ["origin/master", "1.0", "1.1", "1.2", "1.3", "1.4", "1.5", "1.6", "1.7", "1.8", "1.9", "1.10", "1.11", "1.12", "1.13",
               "1.14", "1.15", "1.16", "1.17", "1.18", "1.19", "1.20", "1.21", "1.22", "1.23", "1.24", "1.25", "1.26",
               "1.27", "1.28", "1.29", "1.30", "1.31", "1.32", "1.33", "1.34"]

    g = Gitana(CONFIG, None)
    g.delete_previous_logs()
    # g.init_db("db_cesium")
    # g.create_project("db_cesium", "cesium")
    # print "import git data"
    # g.import_git_data("db_cesium", "cesium", "repo_cesium", "C:\\Users\\atlanmod\\Desktop\\oss\\ants-work\\github-repos\\cesium", references=TARGETS, processes=20)
    # print "import issue tracker"
    # g.import_github_issue_data("db_cesium", "cesium", "repo_cesium", "cesium_it", "AnalyticalGraphicsInc/cesium", GH_TOKENS)
    # g.import_github_pull_request_data("db_cesium", "cesium", "repo_cesium", "cesium_it", "AnalyticalGraphicsInc/cesium", GH_TOKENS)
    # g.match_vcs_and_github_users("db_cesium", "cesium", "repo_cesium", "AnalyticalGraphicsInc/cesium", GH_TOKENS)
    print "import fun data"
    g.import_code_data("db_cesium", "cesium", "repo_cesium", "C:\\Users\\atlanmod\\Desktop\\oss\\ants-work\\github-repos\\cesium", references=["origin/master"], processes=20)


def _decidim():
    g = Gitana(CONFIG, None)
    g.delete_previous_logs()
    g.init_db("db_decidim")
    g.create_project("db_decidim", "decidim")
    print "import git data"
    g.import_git_data("db_decidim", "decidim", "repo_decidim", "C:\\Users\\atlanmod\\Desktop\\decidim-analysis\\decidim", references=["origin/master"])
    g.match_vcs_and_github_users("db_decidim", "decidim", "repo_decidim", "decidim/decidim", GH_TOKENS)
    g.export_json("db_decidim", "repo_decidim", "./decidim-master.json", references=["origin/master"])


def _decidim_hospitalet():
    g = Gitana(CONFIG, None)
    g.delete_previous_logs()
    g.init_db("db_decidim_hospitalet")
    g.create_project("db_decidim_hospitalet", "decidim_hospitalet")
    print "import git data"
    g.import_git_data("db_decidim_hospitalet", "decidim_hospitalet", "repo_decidim_hospitalet", "C:\\Users\\atlanmod\\Desktop\\decidim-analysis\\decidim-hospitalet", references=["origin/master"])
    g.match_vcs_and_github_users("db_decidim_hospitalet", "decidim_hospitalet", "repo_decidim_hospitalet", "HospitaletDeLlobregat/decidim-hospitalet", GH_TOKENS)
    g.export_json("db_decidim_hospitalet", "repo_decidim_hospitalet", "./decidim-hospitalet-master.json", references=["origin/master"])


def _get_data(db_name, project_name, repo_name, issue_tracker_name, repo_path, github_name):
    g = Gitana(CONFIG, None)
    g.delete_previous_logs()
    g.init_db(db_name)
    g.create_project(db_name, project_name)
    print "import git data"
    g.import_git_data(db_name, project_name, repo_name, repo_path, references=["origin/master"]) #, "v1.0.0", "v1.1.0", "v1.2.0", "v1.3.0", "v1.4.0", "v2.0.0", "v2.1.0", "v2.2.0", "v2.3.0", "v.3.0.0", "v.3.1.0", "v.3.2.0", "v.3.3.0"])
    print "import issue tracker"
    g.import_github_issue_data(db_name, project_name, repo_name, issue_tracker_name, github_name, GH_TOKENS)
    g.import_github_pull_request_data(db_name, project_name, repo_name, issue_tracker_name, github_name, GH_TOKENS)
    g.match_vcs_and_github_users(db_name, project_name, repo_name, github_name, GH_TOKENS)
    print "import fun data"
    g.import_code_data(db_name, project_name, repo_name, repo_path, references=["origin/master"], processes=5)


def main():
    #_papyrus()
    _cesiumjs()
    #_decidim()
    #_decidim_hospitalet()

    # _get_data("db_metascience", "metascience", "repo_metascience", "metascience_it", "C:\\Users\\atlanmod\\Desktop\\oss\\ants-work\\github-repos\\metaScience", "SOM-Research/metaScience")
    #_get_data("db_pygithub", "pygithub", "repo_pygithub", "pygithub_it", "C:\\Users\\atlanmod\\Desktop\\oss\\ants-work\\github-repos\\PyGitHub", "PyGithub/PyGithub")
    #_get_data("db_2048", "2048", "repo_2048", "2048_it", "C:\\Users\\atlanmod\\Desktop\\oss\\ants-work\\github-repos\\2048", "gabrielecirulli/2048")
    # _get_data("db_x_ray", "x_ray", "repo_x_ray", "x_ray_it", "C:\\Users\\atlanmod\\Desktop\\oss\\ants-work\\github-repos\\x-ray", "matthewmueller/x-ray")
    # _get_data("db_jquery", "jquery", "repo_jquery", "jquery_it", "C:\\Users\\atlanmod\\Desktop\\oss\\ants-work\\github-repos\\jquery", "jquery/jquery")
    # _get_data("db_musicindicator", "musicindicator", "repo_musicindicator", "musicindicator_it", "C:\\Users\\atlanmod\\Desktop\\oss\\ants-work\\github-repos\\MusicIndicator", "Taishi-Y/MusicIndicator")
    #_get_data("db_javaparser", "javaparser", "repo_javaparser", "javaparser_it", "C:\\Users\\atlanmod\\Desktop\\oss\\ants-work\\github-repos\\javaparser", "javaparser/javaparser")
    # _get_data("db_grimoire_sortinghat", "sortinghat", "repo_sortinghat", "sortinghat_it", "C:\\Users\\atlanmod\\Desktop\\oss\\ants-work\\github-repos\\sortinghat", "grimoirelab/sortinghat")
    # _get_data("db_grimoire_perceval", "perceval", "repo_perceval", "perceval_it", "C:\\Users\\atlanmod\\Desktop\\oss\\ants-work\\github-repos\\perceval", "grimoirelab/perceval")
    # _get_data("db_grimoire_panels", "panels", "repo_panels", "panels_it", "C:\\Users\\atlanmod\\Desktop\\oss\\ants-work\\github-repos\\panels", "grimoirelab/panels")
    # _get_data("db_grimoire_mordred", "mordred", "repo_mordred", "mordred_it", "C:\\Users\\atlanmod\\Desktop\\oss\\ants-work\\github-repos\\mordred", "grimoirelab/mordred")
    # _get_data("db_grimoire_GrimoireELK", "GrimoireELK", "repo_GrimoireELK", "GrimoireELK_it", "C:\\Users\\atlanmod\\Desktop\\oss\\ants-work\\github-repos\\GrimoireELK", "grimoirelab/GrimoireELK")
    # _get_data("db_grimoire_perceval", "perceval", "repo_perceval", "perceval_it", "C:\\Users\\atlanmod\\Desktop\\oss\\ants-work\\github-repos\\perceval", "grimoirelab/perceval")
    #_get_data("db_bootstrap", "bootstrap", "repo_bootstrap", "bootstrap_it", "C:\\Users\\atlanmod\\Desktop\\oss\\ants-work\\github-repos\\bootstrap", "twbs/bootstrap")
    #_get_data("db_javasymbolsolver", "javasymbolsolver", "repo_javasymbolsolver", "javasymbolsolver_it", "C:\\Users\\atlanmod\\Desktop\\oss\\ants-work\\github-repos\\javasymbolsolver", "javaparser/javasymbolsolver")

if __name__ == "__main__":
    main()
