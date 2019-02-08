#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

from datetime import datetime
import multiprocessing

from querier_git import GitQuerier
from importers.vcs.git.code2db_extract_commit_file import Code2DbCommitFile
from util import multiprocessing_util
from git_dao import GitDao
from util.logging_util import LoggingUtil


class Code2DbUpdate():
    """
    This class handles the update of code data
    """

    NUM_PROCESSES = 5

    def __init__(self, db_name, project_name,
                 repo_name, git_repo_path, extensions, references,
                 num_processes, config, log_root_path):
        """
        :type db_name: str
        :param db_name: the name of an existing DB

        :type project_name: str
        :param project_name: the name of an existing project in the DB

        :type repo_name: str
        :param repo_name: the name of the Git repository to import

        :type git_repo_path: str
        :param git_repo_path: the local path of the Git repository

        :type extensions: list str
        :param extensions: file extensions to analyse. Currently extensions supported: ['java', 'py', 'php', 'scala', 'js', 'rb', 'cs', 'cpp', 'c']

        :type references: list str
        :param references: list of references to analyse

        :type num_processes: int
        :param num_processes: number of processes to import the data (default 5)

        :type config: dict
        :param config: the DB configuration file

        :type log_root_path: str
        :param log_root_path: the log path
        """
        self._log_path = log_root_path + "update-code-" + db_name + "-" + project_name + "-" + repo_name
        self._git_repo_path = git_repo_path
        self._project_name = project_name
        self._db_name = db_name
        self._repo_name = repo_name
        self._extensions = extensions
        self._references = references

        if num_processes:
            self._num_processes = num_processes
        else:
            self._num_processes = Code2DbUpdate.NUM_PROCESSES

        config.update({'database': db_name})
        self._config = config

        self._logging_util = LoggingUtil()

        self._logger = None
        self._fileHandler = None
        self._querier = None
        self._dao = None

    def _get_new_commit_file_pairs(self, repo_id):
        pairs = []

        filter_references = "1 = 1"
        if self._references:
            filter_references = "r.name IN (" + ",".join(["'" + e + "'" for e in self._references]) + ")"
        filter_extensions = "1 = 1"
        if self._extensions:
            filter_extensions = "f.ext IN (" + ",".join(["'" + e + "'" for e in self._extensions]) + ")"

        cursor = self._dao.get_cursor()
        query = "SELECT existing_pairs.* " \
                "FROM ( " \
                "SELECT cac.commit_id, cac.file_id FROM code_at_commit cac GROUP BY cac.commit_id, cac.file_id) AS processed_pairs " \
                "RIGHT JOIN " \
                "(SELECT c.id as commit_id, c.sha, f.id AS file_id, f.name AS file_name, f.ext AS file_ext " \
                "FROM commit_in_reference cin JOIN reference r ON r.id = cin.ref_id " \
                "JOIN commit c ON c.id = cin.commit_id " \
                "JOIN file_modification fm ON fm.commit_id = c.id " \
                "JOIN file f ON f.id = fm.file_id " \
                "WHERE " + filter_references + " AND " + filter_extensions + " AND cin.repo_id = %s " \
                "GROUP BY c.id, f.id) AS existing_pairs " \
                "ON processed_pairs.commit_id = existing_pairs.commit_id AND processed_pairs.file_id = existing_pairs.file_id " \
                "WHERE processed_pairs.commit_id IS NULL"
        arguments = [repo_id]
        self._dao.execute(cursor, query, arguments)

        row = self._dao.fetchone(cursor)

        while row:
            pairs.append({"commit_id": row[0], "commit_sha": row[1], "file_id": row[2], "file_name": row[3], "file_ext": row[4]})
            row = self._dao.fetchone(cursor)
        self._dao.close_cursor(cursor)

        return pairs

    def _update_existing_references(self, repo_id, import_type):
        pairs = self._get_new_commit_file_pairs(repo_id)
        intervals = [i for i in multiprocessing_util.get_tasks_intervals(pairs, self._num_processes) if len(i) > 0]

        queue_intervals = multiprocessing.JoinableQueue()
        results = multiprocessing.Queue()

        # Start consumers
        multiprocessing_util.start_consumers(self._num_processes, intervals, results)

        for interval in intervals:
            issue_extractor = Code2DbCommitFile(self._db_name, self._git_repo_path, interval, import_type,
                                                self._config, self._log_path)
            queue_intervals.put(issue_extractor)

        # Add end-of-queue markers
        multiprocessing_util.add_poison_pills(self._num_processes, queue_intervals)

        # Wait for all of the tasks to finish
        queue_intervals.join()

    def _update_info_code(self, repo_id, import_type):
        #updates code data
        self._update_existing_references(repo_id, import_type)

    def _get_import_type(self, repo_id):
        #gets import type
        import_type = 0
        import_type += self._dao.function_at_commit_is_empty(repo_id) + self._dao.code_at_commit_is_empty(repo_id)
        return import_type

    def update(self):
        """
        updates the Git data stored in the DB
        """
        try:
            self._logger = self._logging_util.get_logger(self._log_path)
            self._fileHandler = self._logging_util.get_file_handler(self._logger, self._log_path, "info")

            self._logger.info("Code2DbUpdate started")
            start_time = datetime.now()

            self._querier = GitQuerier(self._git_repo_path, self._logger)
            self._dao = GitDao(self._config, self._logger)

            project_id = self._dao.select_project_id(self._project_name)
            repo_id = self._dao.select_repo_id(self._repo_name)
            self._update_info_code(repo_id, self._get_import_type(repo_id))

            end_time = datetime.now()
            minutes_and_seconds = self._logging_util.calculate_execution_time(end_time, start_time)
            self._logger.info("Code2DbUpdate finished after " + str(minutes_and_seconds[0])
                            + " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
            self._logging_util.remove_file_handler_logger(self._logger, self._fileHandler)
        except:
            self._logger.error("Code2DbUpdate failed", exc_info=True)
        finally:
            if self._dao:
                self._dao.close_connection()