__author__ = 'valerio cosentino'

from util.logging_util import LoggingUtil
from querier_git import GitQuerier
from querier_code import CodeQuerier
from git_dao import GitDao
from datetime import datetime
import re
import codecs
import os


class Code2DbCommitFile():
    """
    This class handles the import of code function data for a set of commit file pairs
    """

    #import overall function statistics per file
    LIGHT_IMPORT_TYPE = 1
    #import import function-level information
    FULL_IMPORT_TYPE = 2

    def __init__(self, db_name, git_repo_path, interval, import_type,
                 config, log_root_path):
        """
        :type db_name: str
        :param db_name: the name of an existing DB

        :type git_repo_path: str
        :param git_repo_path: local path of the Git repository

        :type interval: list dict
        :param interval: a list of commit file pair

        :type import_type: int
        :param import_type: 1 = import overall function statistics per file, 2 = import function-level information

        :type config: dict
        :param config: the DB configuration file

        :type log_root_path: str
        :param log_root_path: the log path
        """
        self._log_root_path = log_root_path
        self._git_repo_path = git_repo_path
        self._db_name = db_name
        self._interval = interval
        self._import_type = import_type
        self._config = config
        self._fileHandler = None
        self._logger = None
        self._git_querier = None
        self._code_querier = None
        self._dao = None
        self._tmp_root_file = None

    def __call__(self):
        self._logging_util = LoggingUtil()
        log_path = self._log_root_path + "-code2db-" + str(self._interval[0].get('commit_id')) + "_" + str(self._interval[0].get('file_id')) + "-" + str(self._interval[-1].get('commit_id')) + "_" + str(self._interval[-1].get('file_id'))
        self._logger = self._logging_util.get_logger(log_path)
        self._fileHandler = self._logging_util.get_file_handler(self._logger, log_path, "info")

        try:
            self._tmp_root_file = log_path + "-tmp."
            self._git_querier = GitQuerier(self._git_repo_path, self._logger)
            self._code_querier = CodeQuerier(self._logger, self._tmp_root_file + "txt")
            self._dao = GitDao(self._config, self._logger)
            self.extract()
        except Exception:
            self._logger.error("Code2DbTag failed", exc_info=True)
        finally:
            if self._dao:
                self._dao.close_connection()

    def _save_content(self, content, target):
        file = codecs.open(target, "w+", "utf-8")
        file.write(content)
        file.close()

    def _delete_tmp_files(self, targets):
        for target in targets:
            if os.path.exists(target):
                os.remove(target)

    def _process_commit_file(self):
        _tmp_files = set()
        for i in self._interval:
            try:
                commit_id = i.get("commit_id")
                commit_sha = i.get("commit_sha")
                file_id = i.get("file_id")
                file_name = i.get("file_name")
                file_ext = i.get("file_ext")

                found = self._dao.select_code_at_commit(commit_id, file_id)
                if file_ext not in CodeQuerier.FORBIDDEN_EXTENSIONS and not found:
                    check_extension = False
                    if file_ext in CodeQuerier.ALLOWED_EXTENSIONS:
                        check_extension = True

                    if not file_ext:
                        file_ext = "unknown"

                    _tmp_file = self._tmp_root_file + file_ext
                    _tmp_files.add(_tmp_file)

                    file_content_at_revision = self._git_querier.get_file_content(commit_sha, file_name)
                    if file_content_at_revision:
                        self._save_content(file_content_at_revision, _tmp_file)

                        if check_extension:
                            file_info, fun_info = self._code_querier.get_complexity_info(_tmp_file, self._import_type)
                            self._dao.insert_code_at_commit(commit_id, file_id, file_info.get('ccn'),
                                                            file_info.get('loc'), file_info.get('comments'),
                                                            file_info.get('blanks'), file_info.get('funs'),
                                                            file_info.get('tokens'), file_info.get('avg_ccn'),
                                                            file_info.get('avg_loc'), file_info.get('avg_tokens'))

                            if self._import_type == Code2DbCommitFile.FULL_IMPORT_TYPE:
                                for fi in fun_info:
                                    self._dao.insert_function(fi.get('name'), file_id, fi.get('args'),
                                                              fi.get('loc'), fi.get('tokens'), fi.get('lines'),
                                                              fi.get('ccn'), fi.get('start'), fi.get('end'))

                                    fun_id = self._dao.select_function_id(file_id, fi.get('start'), fi.get('end'))

                                    self._dao.insert_function_at_commit(fun_id, commit_id)

                        else:
                            file_info = self._code_querier.get_comment_info(_tmp_file)
                            self._dao.insert_code_at_commit(commit_id, file_id, None,
                                                            file_info.get('loc'), file_info.get('comments'),
                                                            file_info.get('blanks'), None, None, None, None, None)

                    if len(_tmp_files) >= 20:
                        self._delete_tmp_files(_tmp_files)

            except Exception:
                self._logger.error("Code2DbCommitFile failed on pair " + str(commit_sha) + ", " + str(file_name), exc_info=True)

        if _tmp_files:
            self._delete_tmp_files(_tmp_files)

    def extract(self):
        """
        extracts code function data and stores it in the DB
        """
        try:
            self._logger.info("Code2DbCommitFile started")
            start_time = datetime.now()

            self._process_commit_file()

            end_time = datetime.now()
            minutes_and_seconds = self._logging_util.calculate_execution_time(end_time, start_time)
            self._logger.info("Code2DbCommitFile finished after " + str(minutes_and_seconds[0])
                            + " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
            self._logging_util.remove_file_handler_logger(self._logger, self._fileHandler)
        except Exception, e:
            self._logger.error("Code2DbCommitFile failed", exc_info=True)
