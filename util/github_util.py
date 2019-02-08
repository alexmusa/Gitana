#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

from importers.vcs.git.git_dao import GitDao
from importers.issue_tracker.github.querier_github import GitHubQuerier
from util.logging_util import LoggingUtil
from util.db_util import DbUtil
from datetime import datetime


class GitHubUtil():
    """
    This class helps mapping the identities of the users in the vcs and GitHub
    """
    def __init__(self, db_name, project_name,
                 repo_name, github_repo_full_name, tokens,
                 config, log_root_path):
        """
        :type db_name: str
        :param db_name: the name of an existing DB

        :type project_name: str
        :param project_name: the name of an existing project in the DB

        :type repo_name: str
        :param repo_name: the name of an existing repository in the DB

        :type url: str
        :param url: full name of the GitHub repository

        :type tokens: list str
        :param token: list of GitHub tokens

        :type config: dict
        :param config: the DB configuration file

        :type log_root_path: str
        :param log_root_path: the log path
        """
        self._log_path = log_root_path + "map-vcs-github-users-" + db_name + "-" + project_name + "-" + repo_name
        self._project_name = project_name
        self._db_name = db_name
        self._repo_name = repo_name
        self._tokens = tokens
        self._active_token = 0
        self._url = github_repo_full_name

        config.update({'database': db_name})
        self._config = config

        self._logging_util = LoggingUtil()
        self._logger = self._logging_util.get_logger(self._log_path)
        self._db_util = DbUtil()
        self._cnx = self._db_util.get_connection(self._config)
        self._git_dao = GitDao(self._config, self._logger)
        self._github_querier = GitHubQuerier(self._url, self._tokens[self._active_token], self._logger)

    def _change_token(self):
        if len(self._tokens) > 1:
            if not self._github_querier._token_util._is_usuable(self._tokens[self._active_token]):
                self._active_token = (self._active_token + 1) % len(self._tokens)
                self._github_querier = GitHubQuerier(self._url, self._tokens[self._active_token], self._logger)

    def _analyse_user(self, user, unmatched_user, sha):
        if user:
            user_name = self._github_querier.get_user_name(user)
            user_ids = self._db_util.select_all_user_ids_by_name(self._cnx, user_name, self._logger)

            for user_id in user_ids:
                try:
                    user_id, alias_id = self._db_util._identify_user_and_alias(self._cnx, unmatched_user, user_id, self._logger)
                    if user_id != alias_id:
                        self._db_util.insert_user_alias(self._cnx, user_id, alias_id, self._logger)
                        self._logger.info("user ids " + str(user_id) + " and " + str(alias_id) + " successfully matched")
                except Exception:
                    self._logger.error("user ids " + str(user_id) + " and " + str(alias_id) + " not matched", exc_info=True)
                    continue
        else:
            self._logger.warning("GitHub user not found for commit " + sha)

    def match(self):
        """
        matches GitHub and Git identities
        """
        try:

            self._fileHandler = self._logging_util.get_file_handler(self._logger, self._log_path, "info")

            self._logger.info("GitHubUtil started")
            start_time = datetime.now()
            repo_id = self._git_dao.select_repo_id(self._repo_name)
            user_ids = self._git_dao.select_all_developer_ids(repo_id)
            alias_ids = self._db_util.select_all_aliased_user_ids(self._cnx, self._logger)
            unmatched_users = list(set(user_ids) - set(alias_ids))

            for unmatched_user in unmatched_users:
                matched = False
                sha = self._git_dao.select_sha_commit_by_user(unmatched_user, repo_id, match_on="author")
                if sha:
                    author = self._github_querier.get_author_by_commit(sha)
                    self._analyse_user(author, unmatched_user, sha)
                    matched = True
                else:
                    sha = self._git_dao.select_sha_commit_by_user(unmatched_user, repo_id, match_on="committer")
                    if sha:
                        committer = self._github_querier.get_committer_by_commit(sha)
                        self._analyse_user(committer, unmatched_user, sha)
                        matched = True

                if not matched:
                    self._logger.warning("No commits found for user " + str(unmatched_user))

            end_time = datetime.now()
            minutes_and_seconds = self._logging_util.calculate_execution_time(end_time, start_time)
            self._logger.info("GitHubUtil finished after " + str(minutes_and_seconds[0])
                            + " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
            self._logging_util.remove_file_handler_logger(self._logger, self._fileHandler)

        except:
            self._logger.error("GitHubUtil failed", exc_info=True)
        finally:
            if self._git_dao:
                self._git_dao.close_connection()

            if self._cnx:
                self._db_util.close_connection(self._cnx)