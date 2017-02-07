#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

from datetime import datetime
import re

from querier_github import GitHubQuerier
from util.date_util import DateUtil
from github_dao import GitHubDao
from util.logging_util import LoggingUtil


class GitHubIssue2Db(object):
    def __init__(self, db_name,
                 repo_id, issue_tracker_id, url, interval, token,
                 config, log_root_path):
        self._log_root_path = log_root_path
        self._url = url
        self._db_name = db_name
        self._repo_id = repo_id
        self._issue_tracker_id = issue_tracker_id
        self._interval = interval
        self._token = token
        self._config = config

        self._logging_util = LoggingUtil()
        self._date_util = DateUtil()

        self._fileHandler = None
        self._logger = None
        self._querier = None
        self._dao = None

    def __call__(self):
        try:
            log_path = self._log_root_path + "-issue2db-" + str(self._interval[0]) + "-" + str(self._interval[-1])
            self._logger = self._logging_util.get_logger(log_path)
            self._fileHandler = self._logging_util.get_file_handler(self._logger, log_path, "info")

            self._querier = GitHubQuerier(self._url, self._token, self._logger)
            self._dao = GitHubDao(self._config, self._logger)
            self.extract()
        except Exception, e:
            self._logger.error("GitHubIssue2Db failed", exc_info=True)
        finally:
            if self._dao:
                self._dao.close_connection()

    def _insert_attachments(self, attachments, message_id):
        pos = 0
        for attachment in attachments:
            attachment_name = self._querier.get_attachment_name(attachment)
            attachment_own_id = self._querier.generate_attachment_id(message_id, pos)
            attachment_url = self._querier.get_attachment_url(attachment)
            self._dao.insert_attachment(attachment_own_id, message_id, attachment_name, attachment_url)
            pos += 1

    def _find_mentioner_user(self, issue_id, created_at):
        creator = None
        issue = self._querier.get_issue(issue_id)
        found = [c for c in self._querier.get_issue_comments(issue) if c.created_at == created_at]

        if len(found) == 1:
            creator = found[0].user
        else:
            self._logger.warning("multiple mentioner users")

        return creator

    def _extract_history(self, issue_id, history):
        for event in history:
            try:
                created_at = self._querier.get_event_creation_time(event)
                actor = self._querier.get_event_actor(event)
                actor_id = self._dao.get_user_id(self._querier.get_user_name(actor), self._querier.get_user_email(actor))
                action = event.event

                if action in ["opened", "edited", "closed", "reopened"]:
                    self._dao.insert_event_type(action)
                    event_type_id = self._dao.select_event_type(action)
                    self._dao.insert_issue_event(issue_id, event_type_id, action, actor_id, created_at, None)
                elif action in ["labeled", "unlabeled"]:
                    self._dao.insert_event_type(action)
                    event_type_id = self._dao.select_event_type(action)
                    self._dao.insert_issue_event(issue_id, event_type_id, event._rawData.get('label').get('name').lower(), actor_id, created_at, None)
                elif action in ["mentioned"]:
                    self._dao.insert_event_type(action)
                    event_type_id = self._dao.select_event_type(action)
                    user_mentioner = self._find_mentioner_user(issue_id, created_at)
                    user_id = self._dao.get_user_id(self._querier.get_user_name(user_mentioner), self._querier.get_user_email(user_mentioner))
                    self._dao.insert_issue_event(issue_id, event_type_id, self._querier.get_user_name(user_mentioner), user_id, created_at, actor_id)
                elif action in ["subscribed"]:
                    self._dao.insert_event_type(action)
                    event_type_id = self._dao.select_event_type(action)
                    self._dao.insert_issue_event(issue_id, event_type_id, action, actor_id, created_at, None)
                elif action in ["assigned", "unassigned"]:
                    self._dao.insert_event_type(action)
                    event_type_id = self._dao.select_event_type(action)

                    assignee_login = event._rawData.get('assignee').get('login')
                    assignee = self._querier.find_user(assignee_login)
                    if assignee:
                        assignee_id = self._dao.get_user_id(self._querier.get_user_name(assignee), self._querier.get_user_email(assignee))
                    else:
                        assignee_id = self._dao.get_user_id(assignee_login, None)

                    assigner_login = event._rawData.get('assigner').get('login')
                    assigner = self._querier.find_user(assigner_login)
                    if assigner:
                        assigner_id = self._dao.get_user_id(self._querier.get_user_name(assigner), self._querier.get_user_email(assigner))
                    else:
                        assignee_id = self._dao.get_user_id(assigner_login, None)

                    self._dao.insert_issue_event(issue_id, event_type_id, action, assigner_id, created_at, assignee_id)


            except Exception, e:
                self._logger.warning("event at (" + str(created_at) + ") not extracted for issue id: " + str(issue_id) + " - tracker id " + str(self._issue_tracker_id), exc_info=True)

    def _extract_subscribers(self, issue_id, subscribers):
        for subscriber in subscribers:
            try:
                subscriber_id = self._dao.get_user_id(self._querier.get_user_name(subscriber), self._querier.get_user_email(subscriber))
                self._dao.insert_subscriber(issue_id, subscriber_id)
            except Exception, e:
                self._logger.warning("subscriber (" + subscriber.login + ") not inserted for issue id: " + str(issue_id) + " - tracker id " + str(self._issue_tracker_id), exc_info=True)

    def _extract_assignees(self, issue_id, assignees):
        for assignee in assignees:
            try:
                assignee_login = assignee.get('login')
                assignee = self._querier.find_user(assignee_login)

                if assignee:
                    assignee_id = self._dao.get_user_id(self._querier.get_user_name(assignee), self._querier.get_user_email(assignee))
                else:
                    assignee_id = self._dao.get_user_id(assignee_login, None)

                self._dao.insert_assignee(issue_id, assignee_id)
            except Exception, e:
                self._logger.warning("assignee (" + assignee.login + ") not inserted for issue id: " + str(issue_id) + " - tracker id " + str(self._issue_tracker_id), exc_info=True)

    def _extract_first_comment(self, issue_id):
        issue = self._querier.get_issue(issue_id)
        created_at = self._querier.get_issue_creation_time(issue)
        author = self._querier.get_issue_creator(issue)
        author_id = self._dao.get_user_id(self._querier.get_user_name(author), self._querier.get_user_email(author))
        body = self._querier.get_issue_body(issue)
        self._dao.insert_issue_comment(0, 0, self._dao.get_message_type_id("comment"), issue_id, body, None, author_id, created_at)

    def _extract_comments(self, issue_id, comments):
        self._extract_first_comment(issue_id)
        pos = 1
        for comment in comments:
            try:
                own_id = self._querier.get_issue_comment_id(comment)
                body = self._querier.get_issue_comment_body(comment)
                author = self._querier.get_issue_comment_author(comment)
                author_id = self._dao.get_user_id(self._querier.get_user_name(author), self._querier.get_user_email(author))
                created_at = self._querier.get_issue_comment_creation_time(comment)
                self._dao.insert_issue_comment(own_id, pos, self._dao.get_message_type_id("comment"), issue_id, body, None, author_id, created_at)

                attachments = self._querier.get_attachments(body)
                if attachments:
                    issue_comment_id = self._dao.select_issue_comment_id(own_id, issue_id, created_at)
                    self._insert_attachments(attachments, issue_comment_id)
            except Exception, e:
                self._logger.warning("comment(" + str(pos) + ") not extracted for issue id: " + str(issue_id) + " - tracker id " + str(self._issue_tracker_id), exc_info=True)
                continue

            pos += 1

    def _extract_labels(self, issue_id, labels):
        for label in labels:
            try:
                digested_label = re.sub("^\W+", "", re.sub("\W+$", "", label.lower()))
                self._dao.insert_label(digested_label.strip())
                label_id = self._dao.select_label_id(digested_label)
                self._dao.assign_label_to_issue(issue_id, label_id)
            except Exception, e:
                self._logger.warning("label (" + label + ") not extracted for issue id: " + str(issue_id) + " - tracker id " + str(self._issue_tracker_id), exc_info=True)

    def _extract_issue_commit_dependency(self, issue_id, commits):
        for id in commits:
            commit_id = self._dao.select_commit(id, self._repo_id)
            if commit_id:
                self._dao.insert_issue_commit_dependency(issue_id, commit_id)

    def _get_issue_info(self, issue_own_id):
        flag_insert_issue_data = False

        issue = self._querier.get_issue(issue_own_id)
        summary = self._querier.get_issue_summary(issue)
        component = None
        version = self._querier.get_issue_version(issue)
        hardware = None
        priority = None
        severity = None
        created_at = self._querier.get_issue_creation_time(issue)
        last_change_at = self._querier.get_issue_last_change_time(issue)

        reference_id = self._dao.find_reference_id(version, issue_own_id, self._repo_id)
        user = self._querier.get_issue_creator(issue)
        user_id = self._dao.get_user_id(self._querier.get_user_name(user), self._querier.get_user_email(user))

        stored_issue_last_change = self._dao.select_last_change_issue(issue_own_id, self._issue_tracker_id, self._repo_id)
        if stored_issue_last_change:
            if last_change_at != stored_issue_last_change:
                flag_insert_issue_data = True
                self._dao.update_issue(issue_own_id, self._issue_tracker_id, summary, component, version, hardware, priority, severity, reference_id, last_change_at)
        else:
            flag_insert_issue_data = True
            self._dao.insert_issue(issue_own_id, self._issue_tracker_id, summary, component, version, hardware, priority, severity, reference_id, user_id, created_at, last_change_at)

        if flag_insert_issue_data:
            issue_id = self._dao.select_issue_id(issue_own_id, self._issue_tracker_id, self._repo_id)

            try:
                self._extract_labels(issue_id, self._querier.get_issue_tags(issue))
            except Exception, e:
                self._logger.error("GitHubError when extracting tags for issue id: " + str(issue_id) + " - tracker id " + str(self._issue_tracker_id), exc_info=True)

            try:
                self._extract_comments(issue_id, self._querier.get_issue_comments(issue))
            except Exception, e:
                self._logger.error("GitHubError when extracting comments for issue id: " + str(issue_id) + " - tracker id " + str(self._issue_tracker_id), exc_info=True)

            try:
                issue_history = self._querier.get_issue_history(issue)
                self._extract_history(issue_id, issue_history)
                self._extract_subscribers(issue_id, self._querier.get_issue_subscribers(issue_history))
                self._extract_assignees(issue_id, self._querier.get_issue_assignees(issue_history))
                self._extract_issue_commit_dependency(issue_id, self._querier.get_commit_dependencies(issue_history))
            except Exception, e:
                self._logger.error("GitHubError when extracting history for issue id: " + str(issue_id) + " - tracker id " + str(self._issue_tracker_id), exc_info=True)

    def _get_issues(self):
        for issue_id in self._interval:
            try:
                self._get_issue_info(issue_id)
            except Exception, e:
                self._logger.error("something went wrong for issue id: " + str(issue_id) + " - tracker id " + str(self._issue_tracker_id), exc_info=True)

    def extract(self):
        try:
            self._logger.info("GitHubIssue2Db started")
            start_time = datetime.now()
            self._get_issues()

            end_time = datetime.now()
            minutes_and_seconds = self._logging_util.calculate_execution_time(end_time, start_time)
            self._logger.info("GitHubIssue2Db finished after " + str(minutes_and_seconds[0])
                           + " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
            self._logging_util.remove_file_handler_logger(self._logger, self._fileHandler)
        except Exception, e:
            self._logger.error("GitHubIssue2Db failed", exc_info=True)
        finally:
            if self._dao:
                self._dao.close_connection()
