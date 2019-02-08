#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

from importers.vcs.git.git_dao import GitDao
from util.logging_util import LoggingUtil
from util.date_util import DateUtil
from datetime import datetime
from diff_match_patch import diff_match_patch
import re


class FileUtil():
    """
    This class provides utilities for the files stored in the Gitana DB
    """
    def __init__(self, config, logger):
        """
        :type config: dict
        :param config: the DB configuration file

        :type logger: Object
        :param logger: logger
        """
        self._config = config
        self._logger = logger
        self._git_dao = GitDao(self._config, self._logger)
        self._date_util = DateUtil()

    def _get_directory_path(self, path_elements):
        directory_path = ''
        path_elements.reverse()
        for p in path_elements:
            directory_path = directory_path + p + '/'

        return directory_path

    def get_directories(self, file_path):
        """
        extracts the directories where the file is located

        :type file_path: str
        :param file_path: path of the file
        """
        directories = []
        dir = file_path.split('/')[:-1]
        dir.reverse()

        for d in range(0, len(dir)):
            dir_path = self._get_directory_path(dir[d:])
            directories.append(dir_path)

        if not directories:
            directories.append("/")

        return directories

    def _process_date(self, d):
        if d:
            if not self._date_util.check_format_timestamp(d, "%Y-%m-%d"):
                d = None
                self._logger.warning("the date " + str(d) + " does not follow the pattern %Y-%m-%d, all changes be retrieved")

        return d

    def get_file_history_by_id(self, file_id, ref_id, reversed=False, before_date=None):
        """
        get file history for a given file id within a reference and before a given date

        :type file_id: int
        :param file_id: the id of the target file

        :type ref_id: str
        :param ref_id: the id of the reference

        :type reversed: bool
        :param reversed: if True, it returns the changes from the most recent to the earliest

        :type before_date: str (YYYY-mm-dd)
        :param before_date: if not null, it returns the last version of the file before the given date
        """
        before_date = self._process_date(before_date)

        previous_renamings = [file_id]

        changes = self._git_dao.select_file_changes(file_id, ref_id, before_date, patch=False, code=True)
        renamings_to_process = self._git_dao.select_file_renamings(file_id, ref_id)

        if renamings_to_process:
            while renamings_to_process != []:
                current_renamings = renamings_to_process
                for previous_file_id in current_renamings:
                    changes = changes + self._git_dao.select_file_changes(previous_file_id, ref_id, before_date)
                    previous_renamings.append(previous_file_id)
                    renamings_to_process = renamings_to_process + self._git_dao.select_file_renamings(previous_file_id, ref_id)
                renamings_to_process = list(set(renamings_to_process) - set(previous_renamings))

        return sorted(changes, key=lambda k: k['authored_date'], reverse=reversed)

    def get_file_history_by_name(self, repo_name, file_name, reference_name, reversed=False, before_date=None):
        """
        get file history for a given file name within a reference and before a given date

        :type repo_name: str
        :param repo_name: the name of the repository to import. It cannot be null

        :type file_name: dict
        :param file_name: the name of the target file

        :type reference_name: str
        :param reference_name: the name of the reference

        :type reversed: bool
        :param reversed: if True, it returns the changes from the most recent to the earliest

        :type before_date: str (YYYY-mm-dd)
        :param before_date: if not null, it returns the last version of the file before the given date
        """
        history = []
        try:
            repo_id = self._git_dao.select_repo_id(repo_name)
            file_id = self._git_dao.select_file_id(repo_id, file_name)
            reference_id = self._git_dao.select_reference_id(repo_id, reference_name)
            history = self.get_file_history_by_id(file_id, reference_id, reversed, before_date)
        except:
            self._logger.error("FileUtil failed", exc_info=True)
        finally:
            if self._git_dao:
                self._git_dao.close_connection()

            return history

    def get_file_version_by_id(self, file_id, ref_id, before_date=None):
        """
        get file version for a given file id within a reference and before a given date

        :type file_id: int
        :param file_id: the id of the target file

        :type ref_id: str
        :param ref_id: the id of the reference

        :type before_date: str (YYYY-mm-dd)
        :param before_date: if not null, it returns the last version of the file before the given date
        """
        before_date = self._process_date(before_date)
        changes = self._git_dao.select_file_changes(file_id, ref_id, before_date, patch=True)
        sorted(changes, key=lambda k: k['committed_date'], reverse=False)

        # the digestion is needed because the library diff-match-patch requires that the preamble of the diff information (@@ -.. +.. @@)
        # appears alone in one line. Sometimes GitPython returns such a preamble mixed with other data
        diff_util = diff_match_patch()
        diff_util.Diff_Timeout = 0
        diff_util.Match_Distance = 5000
        diff_util.Match_Threshold = 0.8
        diff_util.Patch_DeleteThreshold = 0.8
        content = ""
        res_merge = []
        for change in changes:
            digested_patches = []
            p = change.get('patch')
            for line in p.split('\n'):
                m = re.match("^@@ -(\d+),?(\d*) \+(\d+),?(\d*) @@", line)
                if m:
                    rest = line.split(m.group())[1]
                    digested_patches.append(m.group())
                    if rest:
                        digested_patches.append(rest.rstrip())
                else:
                    digested_patches.append(line)

            ps = diff_util.patch_fromText("\n".join(digested_patches))
            res = diff_util.patch_apply(ps, content)
            content = res[0]

            res_merge = res_merge + res[1]

        self._logger.info(str(len([r for r in res_merge if r])) + " out of " + str(len(res_merge)) + " patches were successfully used to rebuild the file")

        return content

    def get_file_version_by_name(self, repo_name, file_name, reference_name, before_date=None):
        """
        get file version for a given file name within a reference and before a given date

        :type repo_name: str
        :param repo_name: the name of the repository to import. It cannot be null

        :type file_name: dict
        :param file_name: the name of the target file

        :type reference_name: str
        :param reference_name: the name of the reference

        :type before_date: str (YYYY-mm-dd)
        :param reversed: if not null, it returns the last version of the file before the given date
        """
        content = ""
        try:
            repo_id = self._git_dao.select_repo_id(repo_name)
            file_id = self._git_dao.select_file_id(repo_id, file_name)
            reference_id = self._git_dao.select_reference_id(repo_id, reference_name)

            content = self.get_file_version_by_id(file_id, reference_id, before_date)
        except:
            self._logger.error("FileUtil failed", exc_info=True)
        finally:
            if self._git_dao:
                self._git_dao.close_connection()

            return content


class FileUtilWrapper():
    """
    This class wraps the operations provided by the FileUtil class
    """
    def __init__(self, db_name, config, log_root_path):
        """
        :type db_name: str
        :param db_name: the name of an existing DB

        :type repo_name: str
        :param repo_name: the name of an existing repository in the DB

        :type log_root_path: str
        :param log_root_path: the log path
        """
        self._log_path = log_root_path + "file-util-wrapper" + db_name
        self._db_name = db_name

        config.update({'database': db_name})
        self._config = config

        self._logging_util = LoggingUtil()
        self._logger = self._logging_util.get_logger(self._log_path)

    def get_file_history(self, repo_name, file_name, reference_name, reversed=False, before_date=None):
        """
        get file history for a given file name within a reference. Optionally, the history can be retrieved before a given date

        :type repo_name: str
        :param repo_name: the name of an existing repository in the DB

        :type file_name: dict
        :param file_name: the name of the target file

        :type reference_name: str
        :param reference_name: the name of the reference

        :type reversed: bool
        :param reversed: if True, it returns the changes from the most recent to the earliest

        :type before_date: str (YYYY-mm-dd)
        :param reversed: if not null, it returns the last version of the file before the given date
        """
        history = []
        try:
            self._fileHandler = self._logging_util.get_file_handler(self._logger, self._log_path, "info")
            self._logger.info("FileUtilWrapper started")
            start_time = datetime.now()

            file_util = FileUtil(self._config, self._logger)
            history = file_util.get_file_history_by_name(repo_name, file_name, reference_name, reversed, before_date)

            end_time = datetime.now()
            minutes_and_seconds = self._logging_util.calculate_execution_time(end_time, start_time)
            self._logger.info("FileUtilWrapper finished after " + str(minutes_and_seconds[0])
                            + " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
            self._logging_util.remove_file_handler_logger(self._logger, self._fileHandler)
        except:
            self._logger.error("FileUtilWrapper failed", exc_info=True)
        finally:
            return history

    def get_file_version(self, repo_name, file_name, reference_name, before_date=None):
        """
        get file version for a given file name within a reference. Optionally, the version can be retrieved before a given date

        :type repo_name: str
        :param repo_name: the name of an existing repository in the DB

        :type file_name: dict
        :param file_name: the name of the target file

        :type reference_name: str
        :param reference_name: the name of the reference

        :type before_date: str (YYYY-mm-dd)
        :param reversed: if not null, it returns the last version of the file before the given date
        """
        content = ""
        try:
            self._fileHandler = self._logging_util.get_file_handler(self._logger, self._log_path, "info")
            self._logger.info("FileUtilWrapper started")
            start_time = datetime.now()

            file_util = FileUtil(self._config, self._logger)
            content = file_util.get_file_version_by_name(repo_name, file_name, reference_name, before_date)


            end_time = datetime.now()
            minutes_and_seconds = self._logging_util.calculate_execution_time(end_time, start_time)
            self._logger.info("FileUtilWrapper finished after " + str(minutes_and_seconds[0])
                            + " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
            self._logging_util.remove_file_handler_logger(self._logger, self._fileHandler)
        except:
            self._logger.error("FileUtil failed", exc_info=True)
        finally:
            return content