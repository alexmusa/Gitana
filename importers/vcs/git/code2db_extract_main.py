#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

from datetime import datetime
import multiprocessing

from querier_git import GitQuerier
from git_dao import GitDao
from code2db_extract_commit_file import Code2DbCommitFile
from util import multiprocessing_util
from util.logging_util import LoggingUtil


class Code2DbMain():
    """
    This class handles the import of code information
    """

    NUM_PROCESSES = 5

    def __init__(self, db_name, project_name,
                 repo_name, git_repo_path, import_type, extensions, references, num_processes,
                 config, log_root_path):
        """
        :type db_name: str
        :param db_name: the name of an existing DB

        :type project_name: str
        :param project_name: the name of an existing project in the DB

        :type repo_name: str
        :param repo_name: the name of the Git repository to import

        :type git_repo_path: str
        :param git_repo_path: the local path of the Git repository

        :type import_type: int
        :param import_type: 1 = import overall function statistics per file, 2 = import function-level information

        :type extensions: list str
        :param extensions: file extensions to analyse. Gitana calculates loc, comments and blank lines for most of the files.
        For the following languages ['java', 'py', 'php', 'scala', 'js', 'rb', 'cs', 'cpp', 'c'], Gitana also provides insights about ccn, functions and tokens.

        :type references: list str
        :param references: list of references to analyse

        :type num_processes: int
        :param num_processes: number of processes to import the data (default 10)

        :type config: dict
        :param config: the DB configuration file

        :type log_root_path: str
        :param log_root_path: the log path
        """
        self._log_path = log_root_path + "import-code-" + db_name + "-" + project_name + "-" + repo_name
        self._git_repo_path = git_repo_path
        self._project_name = project_name
        self._db_name = db_name
        self._repo_name = repo_name
        self._import_type = import_type
        self._extensions = extensions
        self._references = references

        if num_processes:
            self._num_processes = num_processes
        else:
            self._num_processes = Code2DbMain.NUM_PROCESSES

        config.update({'database': db_name})
        self._config = config

        self._logging_util = LoggingUtil()

        self._logger = None
        self._fileHandler = None
        self._querier = None
        self._dao = None

    def _get_commit_file_pairs(self, repo_id):
        pairs = []

        filter_references = "1 = 1"
        if self._references:
            filter_references = "r.name IN (" + ",".join(["'" + e + "'" for e in self._references]) + ")"
        filter_extensions = "1 = 1"
        if self._extensions:
            filter_extensions = "f.ext IN (" + ",".join(["'" + e + "'" for e in self._extensions]) + ")"

        cursor = self._dao.get_cursor()
        query = "SELECT c.id AS commit_id, c.sha, f.id AS file_id, f.name AS file_name, f.ext AS file_ext " \
                "FROM commit_in_reference cin JOIN reference r ON r.id = cin.ref_id " \
                "JOIN commit c ON c.id = cin.commit_id " \
                "JOIN file_modification fm ON fm.commit_id = c.id " \
                "JOIN file f ON f.id = fm.file_id " \
                "WHERE " + filter_references + " AND " + filter_extensions + " AND cin.repo_id = %s " \
                "GROUP BY c.id, f.id"
        arguments = [repo_id]
        self._dao.execute(cursor, query, arguments)

        row = self._dao.fetchone(cursor)

        while row:
            pairs.append({"commit_id": row[0], "commit_sha": row[1], "file_id": row[2], "file_name": row[3], "file_ext": row[4]})
            row = self._dao.fetchone(cursor)
        self._dao.close_cursor(cursor)

        return pairs

    def _get_info_code(self, repo_id):
        pairs = self._get_commit_file_pairs(repo_id)
        intervals = [i for i in multiprocessing_util.get_tasks_intervals(pairs, self._num_processes) if len(i) > 0]

        queue_intervals = multiprocessing.JoinableQueue()
        results = multiprocessing.Queue()

        # Start consumers
        multiprocessing_util.start_consumers(self._num_processes, queue_intervals, results)

        for interval in intervals:
            issue_extractor = Code2DbCommitFile(self._db_name, self._git_repo_path, interval, self._import_type,
                                                self._config, self._log_path)
            queue_intervals.put(issue_extractor)

        # Add end-of-queue markers
        multiprocessing_util.add_poison_pills(self._num_processes, queue_intervals)

        # Wait for all of the tasks to finish
        queue_intervals.join()

    def extract(self):
        """
        extracts code function data and stores it in the DB
        """
        try:
            self._logger = self._logging_util.get_logger(self._log_path)
            self._fileHandler = self._logging_util.get_file_handler(self._logger, self._log_path, "info")

            self._logger.info("Code2DbMain started")
            start_time = datetime.now()

            self._querier = GitQuerier(self._git_repo_path, self._logger)
            self._dao = GitDao(self._config, self._logger)

            repo_id = self._dao.select_repo_id(self._repo_name)
            self._get_info_code(repo_id)
            end_time = datetime.now()
            minutes_and_seconds = self._logging_util.calculate_execution_time(end_time, start_time)
            self._logger.info("Code2DbMain finished after " + str(minutes_and_seconds[0])
                            + " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
            self._logging_util.remove_file_handler_logger(self._logger, self._fileHandler)
        except Exception:
            self._logger.error("Code2DbMain failed", exc_info=True)
        finally:
            if self._dao:
                self._dao.close_connection()