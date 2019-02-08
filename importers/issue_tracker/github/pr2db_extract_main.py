#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

from datetime import datetime
import multiprocessing

from pr2db_extract_pull_request import GitHubPullRequest2Db
from querier_github import GitHubQuerier
from util import multiprocessing_util
from github_dao import GitHubDao
from util.logging_util import LoggingUtil


class GitHubPullRequest2DbMain():
    """
    This class handles the import of GitHub pull request data
    """

    NUM_PROCESSES = 1

    def __init__(self, db_name, project_name,
                 repo_name, type, issue_tracker_name, url, before_date, tokens,
                 config, log_root_path):
        """
        :type db_name: str
        :param db_name: the name of an existing DB

        :type project_name: str
        :param project_name: the name of an existing project in the DB

        :type repo_name: str
        :param repo_name: the name of an existing repository in the DB

        :type type: str
        :param type: type of the issue tracker (Bugzilla, GitHub)

        :type issue_tracker_name: str
        :param issue_tracker_name: the name of the issue tracker to import

        :type url: str
        :param url: full name of the GitHub repository

        :type before_date: str
        :param before_date: import data before date (YYYY-mm-dd)

        :type tokens: list str
        :param token: list of GitHub tokens

        :type num_processes: int
        :param num_processes: number of processes to import the data (default 5)

        :type config: dict
        :param config: the DB configuration file

        :type log_root_path: str
        :param log_root_path: the log path
        """
        self._log_path = log_root_path + "import-github-pr-" + db_name + "-" + project_name + "-" + issue_tracker_name
        self._type = type
        self._url = url
        self._project_name = project_name
        self._db_name = db_name
        self._issue_tracker_name = issue_tracker_name
        self._repo_name = repo_name
        self._before_date = before_date
        self._tokens = tokens

        config.update({'database': db_name})
        self._config = config

        self._logging_util = LoggingUtil()

        self._logger = None
        self._fileHandler = None
        self._querier = None
        self._dao = None

    def _pass_list_as_argument(self, elements):
        return '-'.join([str(e) for e in elements])

    def _insert_pull_request_data(self, repo_id, issue_tracker_id):
        #processes pull request data
        imported = self._dao.get_already_imported_pull_request_ids(issue_tracker_id, repo_id)
        prs = list(set(self._querier.get_pull_request_ids(self._before_date)) - set(imported))

        intervals = [i for i in multiprocessing_util.get_tasks_intervals(prs, len(self._tokens)) if len(i) > 0]

        queue_intervals = multiprocessing.JoinableQueue()
        results = multiprocessing.Queue()

        # Start consumers
        multiprocessing_util.start_consumers(len(self._tokens), queue_intervals, results)

        pos = 0
        for interval in intervals:
            pr_extractor = GitHubPullRequest2Db(self._db_name, repo_id, issue_tracker_id, self._url, interval, self._tokens[pos],
                                                self._config, self._log_path)
            queue_intervals.put(pr_extractor)
            pos += 1

        # Add end-of-queue markers
        multiprocessing_util.add_poison_pills(len(self._tokens), queue_intervals)

        # Wait for all of the tasks to finish
        queue_intervals.join()

    def _split_pull_request_extraction(self):
        #splits the pr found according to the number of processes
        project_id = self._dao.select_project_id(self._project_name)
        repo_id = self._dao.select_repo_id(project_id, self._repo_name)
        issue_tracker_id = self._dao.select_issue_tracker_id(repo_id, self._issue_tracker_name)
        self._insert_pull_request_data(repo_id, issue_tracker_id)

    def extract(self):
        """
        extracts GitHub pull request data and stores it in the DB
        """
        try:
            self._logger = self._logging_util.get_logger(self._log_path)
            self._fileHandler = self._logging_util.get_file_handler(self._logger, self._log_path, "info")

            self._logger.info("GitHubPullRequest2DbMain started")
            start_time = datetime.now()

            self._querier = GitHubQuerier(self._url, self._tokens[0], self._logger)
            self._dao = GitHubDao(self._config, self._logger)

            self._split_pull_request_extraction()

            end_time = datetime.now()
            minutes_and_seconds = self._logging_util.calculate_execution_time(end_time, start_time)
            self._logger.info("GitHubPullRequest2DbMain finished after " + str(minutes_and_seconds[0])
                            + " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
            self._logging_util.remove_file_handler_logger(self._logger, self._fileHandler)
        except Exception:
            self._logger.error("GitHubPullRequest2DbMain failed", exc_info=True)
        finally:
            if self._dao:
                self._dao.close_connection()