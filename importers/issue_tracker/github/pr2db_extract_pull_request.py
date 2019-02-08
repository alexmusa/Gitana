#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

from datetime import datetime
import re

from querier_github import GitHubQuerier
from util.date_util import DateUtil
from importers.vcs.git.git_dao import GitDao
from github_dao import GitHubDao
from util.logging_util import LoggingUtil


class GitHubPullRequest2Db(object):
    """
    This class handles the import of GitHub pull requests
    """

    def __init__(self, db_name,
                 repo_id, issue_tracker_id, url, interval, token,
                 config, log_root_path):
        """
        :type db_name: str
        :param db_name: the name of an existing DB

        :type repo_id: int
        :param repo_id: the id of an existing repository in the DB

        :type issue_tracker_id: int
        :param issue_tracker_id: the id of an existing issue tracker in the DB

        :type url: str
        :param url: full name of the GitHub repository

        :type interval: list int
        :param interval: a list of issue ids to import

        :type token: str
        :param token: a GitHub token

        :type config: dict
        :param config: the DB configuration file

        :type log_root_path: str
        :param log_root_path: the log path
        """
        self._log_root_path = log_root_path
        self._url = url
        self._db_name = db_name
        self._repo_id = repo_id
        self._issue_tracker_id = issue_tracker_id
        self._interval = interval
        self._token = token
        self._config = config
        self._fileHandler = None
        self._logger = None
        self._querier = None
        self._dao = None
        self._git_dao = None

    def __call__(self):
        self._logging_util = LoggingUtil()
        self._date_util = DateUtil()
        log_path = self._log_root_path + "-pr2db-" + str(self._interval[0]) + "-" + str(self._interval[-1])
        self._logger = self._logging_util.get_logger(log_path)
        self._fileHandler = self._logging_util.get_file_handler(self._logger, log_path, "info")


        try:
            self._querier = GitHubQuerier(self._url, self._token, self._logger)
            self._dao = GitHubDao(self._config, self._logger)
            self._git_dao = GitDao(self._config, self._logger)
            self.extract()
        except Exception, e:
            self._logger.error("GitHubPullRequest2Db failed", exc_info=True)
        finally:
            if self._dao:
                self._dao.close_connection()

    def _extract_comments(self, pr_id, comments):
        pos = 0
        for comment in comments:
            try:
                own_id = self._querier.get_issue_comment_id(comment)
                body = self._querier.get_issue_comment_body(comment)
                author = self._querier.get_issue_comment_author(comment)
                author_id = self._dao.get_user_id(self._querier.get_user_name(author), self._querier.get_user_email(author))
                created_at = self._querier.get_issue_comment_creation_time(comment)
                self._dao.insert_pull_request_comment(own_id, pos, self._dao.get_message_type_id("comment"), pr_id, body, None, author_id, created_at)

                referred_file = self._querier.get_pull_request_commented_file(comment)
                if referred_file:
                    referred_file_id, file_type = self._dao.get_pull_request_file_id_by_name(referred_file, self._repo_id)
                    comment_id = self._dao.select_pull_request_comment_id(own_id, pr_id)

                    if referred_file_id:
                        if file_type == 'codebase':
                            self._dao.insert_pull_request_review(comment_id, pr_id, referred_file_id, 0)
                        else:
                            self._dao.insert_pull_request_review(comment_id, pr_id, 0, referred_file_id)

            except Exception, e:
                self._logger.warning("comment(" + str(pos) + ") not extracted for pull request id: " + str(pr_id) + " - tracker id " + str(self._issue_tracker_id), exc_info=True)
                continue

            pos += 1

    def _get_ext(self, file_name):
        ext = file_name.split('.')[-1]
        return ext

    # def _extract_history(self, pr_id, pr):
    #     merged = self._querier.get_pull_request_merged(pr)
    #
    #     if merged:
    #         merged_at = self._querier.get_pull_request_merged_at(pr)
    #         merged_by = self._querier.get_pull_request_merged_by(pr)
    #         actor_id = self._dao.get_user_id(self._querier.get_user_name(merged_by), self._querier.get_user_email(merged_by))
    #
    #         self._dao.insert_event_type("merged")
    #         event_type_id = self._dao.select_event_type("merged")
    #         self._dao.insert_issue_event(pr_id, event_type_id, "merged", actor_id, merged_at, None)

    def _get_pull_request_info(self, pr_own_id):
        #processes each single pull request
        flag_insert_pr_data = False

        pr = self._querier.get_pull_request(pr_own_id)
        created_at = pr.created_at
        author = self._querier.get_pull_request_author(pr)
        author_id = self._dao.get_user_id(self._querier.get_user_name(author), self._querier.get_user_email(author))

        pr_state = self._querier.get_pull_request_state(pr)

        pr_ref_id = self._git_dao.select_reference_id(self._repo_id, "origin/" + self._querier.get_pull_request_base(pr))
        merged_at = self._querier.get_pull_request_merged_at(pr)
        merged_by = self._querier.get_pull_request_merged_by(pr)

        merged_by_id = None
        if merged_by:
            merged_by_id = self._dao.get_user_id(self._querier.get_user_name(merged_by), self._querier.get_user_email(merged_by))

        self._dao.insert_pull_request(pr_own_id, author_id, pr_state, pr_ref_id, merged_at, merged_by_id, self._issue_tracker_id, self._repo_id)
        pr_id = self._dao.select_pull_request_id(pr_own_id, self._issue_tracker_id)

        for commit in self._querier.get_pull_request_commits(pr):
            try:
                commit_id = self._git_dao.select_commit_id(commit.sha, self._repo_id)
                if commit_id:
                    self._dao.insert_pull_request_commit(pr_id, commit_id, 0)
                else:
                    self._insert_proposed_commit(commit)
                    proposed_commit_id = self._dao.select_proposed_commit_id(commit.sha, self._repo_id)
                    self._dao.insert_pull_request_commit(pr_id, 0, proposed_commit_id)
                    self._insert_file_information(proposed_commit_id, pr)

            except Exception:
                self._logger.error("GitHubError when extracting commit " + str(commit.sha) + " for pull request id: " + str(pr_id) + " - tracker id " + str(self._issue_tracker_id), exc_info=True)
                continue

        self._extract_comments(pr_id, self._querier.get_pull_request_comments(pr))

    def _insert_file_information(self, proposed_commit_id, pull_request):
        files = self._querier.get_pull_request_files(pull_request)
        for f in files:
            try:
                status = f.status
                additions = f.additions
                deletions = f.deletions
                changes = f.changes
                patch = f.patch

                file_id = self._git_dao.select_file_id(self._repo_id, f.filename)

                if file_id:
                    self._dao.insert_proposed_file_modification(proposed_commit_id, file_id, 0, status, additions, deletions, changes, patch)
                else:
                    self._dao.insert_proposed_file(self._repo_id, f.filename, self._get_ext(f.filename))
                    proposed_file_id = self._dao.select_proposed_file_id(self._repo_id, f.filename)
                    self._dao.insert_proposed_file_modification(proposed_commit_id, 0, proposed_file_id, status, additions, deletions, changes, patch)
            except Exception:
                self._logger.error("GitHubError when extracting files from proposed commit id: " + str(proposed_commit_id) + " - tracker id " + str(self._issue_tracker_id), exc_info=True)
                continue

    def _insert_proposed_commit(self, commit):
        author_id = self._dao.get_user_id(self._querier.get_user_name(commit.author), self._querier.get_user_email(commit.author))
        committer_id = self._dao.get_user_id(self._querier.get_user_name(commit.committer), self._querier.get_user_email(commit.committer))
        commit_info = self._querier.get_pull_request_commit_info(commit)
        self._dao.insert_proposed_commit(self._repo_id, commit.sha, commit_info.message, author_id, committer_id, commit_info.author.date, commit_info.committer.date)

    def _get_pull_requests(self):
        #processes pull requests
        for pr_id in self._interval:
            try:
                self._get_pull_request_info(pr_id)
            except Exception, e:
                self._logger.error("something went wrong for issue id: " + str(pr_id) + " - tracker id " + str(self._issue_tracker_id), exc_info=True)

    def extract(self):
        """
        extracts GitHub pull request data and stores it in the DB
        """
        try:
            self._logger.info("GitHubPullRequest2Db started")
            start_time = datetime.now()
            self._get_pull_requests()

            end_time = datetime.now()
            minutes_and_seconds = self._logging_util.calculate_execution_time(end_time, start_time)
            self._logger.info("GitHubPullRequest2Db finished after " + str(minutes_and_seconds[0])
                           + " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
            self._logging_util.remove_file_handler_logger(self._logger, self._fileHandler)
        except Exception:
            self._logger.error("GitHubPullRequest2Db failed", exc_info=True)
        finally:
            if self._dao:
                self._dao.close_connection()
