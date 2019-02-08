#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

from github import Github
from github import GithubException
from util.date_util import DateUtil
from util.token_util import TokenUtil
import re
import time


class GitHubQuerier():
    """
    This class collects the data available on the GitHub issue tracker via its API
    """
    WAIT = 0.2
    ATTEMPTS = 15

    def __init__(self, url, token, logger):
        """
        :type url: str
        :param url: full name of the GitHub repository

        :type token: str
        :param token: a GitHub token

        :type logger: Object
        :param logger: logger
        """
        try:
            self._logger = logger
            self._url = url
            self._token = token
            self._github = Github(token)
            self._repo = self._load_repo(self._url)
            self._token_util = TokenUtil(self._logger, "github")
            self._date_util = DateUtil()
        except:
            self._logger.error("GitHubQuerier init failed")
            raise

    def _load_repo(self, url):
        #connect to the GitHub API
        try:
            repo = self._github.get_repo(url)
            return repo
        except Exception:
            self._logger.error("GitHubQuerier error loading repository " + url + "- ", exc_info=True)
            raise

    def get_pull_request_ids(self, before_date):
        """
        gets data source pull request ids

        :type before_date: str
        :param before_date: selects pull requests with creation date before a given date (YYYY-mm-dd)
        """
        pr_ids = []
        page_count = 1
        self._token_util.wait_is_usable(self._github)
        last_page = int(self._repo.get_pulls(state="all")._getLastPageUrl().split("page=")[-1])

        while page_count != last_page:
            pull_requests = self._fetch_pull_page(page_count)
            for pr in pull_requests:
                if before_date:
                    if pr.created_at <= self._date_util.get_timestamp(before_date, "%Y-%m-%d"):
                        pr_ids.append(pr.number)
                else:
                    pr_ids.append(pr.number)

            page_count += 1

        if pr_ids:
            pr_ids.sort()

        return pr_ids

    def get_issue_ids(self, before_date):
        """
        gets data source issue ids

        :type before_date: str
        :param before_date: selects issues with creation date before a given date (YYYY-mm-dd)
        """
        issue_ids = []
        page_count = 0
        self._token_util.wait_is_usable(self._github)
        last_page = int(self._repo.get_issues(state="all", direction="asc")._getLastPageUrl().split("page=")[-1])

        while page_count != last_page + 1:
            issues = self._fetch_issue_page(page_count)
            for i in issues:
                if before_date:
                    if i.created_at <= self._date_util.get_timestamp(before_date, "%Y-%m-%d"):
                        issue_ids.append(i.number)
                else:
                    issue_ids.append(i.number)

            page_count += 1

        if issue_ids:
            issue_ids.sort()

        return issue_ids

    def _fetch_issue_page(self, page):
        fetched = []
        flag = True
        i = 0
        while flag and i < GitHubQuerier.ATTEMPTS:
            try:
                self._token_util.wait_is_usable(self._github)
                fetched = self._repo.get_issues(state="all").get_page(page)
                flag = False
            except:
                time.sleep(GitHubQuerier.WAIT)
                i += 1

        return fetched

    def _fetch_pull_page(self, page):
        fetched = []
        flag = True
        i = 0
        while flag and i < GitHubQuerier.ATTEMPTS:
            try:
                self._token_util.wait_is_usable(self._github)
                fetched = self._repo.get_pulls(state="all").get_page(page)
                flag = False
            except:
                time.sleep(GitHubQuerier.WAIT)
                i += 1

        return fetched

    def get_issue(self, issue_id):
        """
        gets issue

        :type issue_id: int
        :param issue_id: data source issue id
        """
        fetched = None
        flag = True
        i = 0
        while flag and i < GitHubQuerier.ATTEMPTS:
            try:
                self._token_util.wait_is_usable(self._github)
                fetched = self._repo.get_issue(issue_id)
                flag = False
            except:
                time.sleep(GitHubQuerier.WAIT)
                i += 1

        return fetched

    def get_pull_request(self, pr_id):
        """
        gets pull request by its id

        :type pr_id: int
        :param pr_id: data source pr id
        """
        fetched = None
        flag = True
        i = 0
        while flag and i < GitHubQuerier.ATTEMPTS:
            try:
                self._token_util.wait_is_usable(self._github)
                fetched = self._repo.get_pull(pr_id)
                flag = False
            except:
                time.sleep(GitHubQuerier.WAIT)
                i += 1

        return fetched

    def get_issue_summary(self, issue):
        """
        gets summary of the issue

        :type issue: Object
        :param issue: the Object representing the issue
        """
        found = None
        flag = True
        i = 0
        while flag and i < GitHubQuerier.ATTEMPTS:
            try:
                found = issue.title
                flag = False
            except:
                time.sleep(GitHubQuerier.WAIT)
                i += 1

        return found

    def get_issue_body(self, issue):
        """
        gets body of the issue

        :type issue: Object
        :param issue: the Object representing the issue
        """
        found = None
        flag = True
        i = 0
        while flag and i < GitHubQuerier.ATTEMPTS:
            try:
                found = issue.body
                flag = False
            except:
                time.sleep(GitHubQuerier.WAIT)
                i += 1

        return found

    def get_pull_request_state(self, pr):
        """
        gets version of the pull request

        :type pr: Object
        :param pr: the Object representing the pull request
        """
        found = None
        flag = True
        i = 0
        while flag and i < GitHubQuerier.ATTEMPTS:
            try:
                found = pr.state
                flag = False
            except:
                time.sleep(GitHubQuerier.WAIT)
                i += 1

        return found

    def get_pull_request_base(self, pr):
        """
        gets the name of the branch where the changes will be pulled into

        :type pr: Object
        :param pr: the Object representing the pull request
        """
        found = None
        flag = True
        i = 0
        while flag and i < GitHubQuerier.ATTEMPTS:
            try:
                self._token_util.wait_is_usable(self._github)
                found = pr.base.ref
                flag = False
            except:
                time.sleep(GitHubQuerier.WAIT)
                i += 1

        return found

    def get_pull_request_merged(self, pr):
        """
        gets whether the pull request has been merged or not

        :type pr: Object
        :param pr: the Object representing the pull request
        """
        found = None
        flag = True
        i = 0
        while flag and i < GitHubQuerier.ATTEMPTS:
            try:
                found = pr.merged
                flag = False
            except:
                time.sleep(GitHubQuerier.WAIT)
                i += 1

        return found

    def get_issue_version(self, issue):
        """
        gets version of the issue

        :type issue: Object
        :param issue: the Object representing the issue
        """
        found = None
        flag = True
        i = 0
        while flag and i < GitHubQuerier.ATTEMPTS:
            try:
                found = issue.milestone.number
                flag = False
            except:
                time.sleep(GitHubQuerier.WAIT)
                i += 1

        return found

    def get_issue_creation_time(self, issue):
        """
        gets creation time of the issue

        :type issue: Object
        :param issue: the Object representing the issue
        """
        found = None
        flag = True
        i = 0
        while flag and i < GitHubQuerier.ATTEMPTS:
            try:
                found = issue.created_at
                flag = False
            except:
                time.sleep(GitHubQuerier.WAIT)
                i += 1

        return found

    def get_issue_last_change_time(self, issue):
        """
        gets last change date of the issue

        :type issue: Object
        :param issue: the Object representing the issue
        """
        found = None
        flag = True
        i = 0
        while flag and i < GitHubQuerier.ATTEMPTS:
            try:
                found = issue.updated_at
                flag = False
            except:
                time.sleep(GitHubQuerier.WAIT)
                i += 1

        return found

    def get_issue_creator(self, issue):
        """
        gets creator of the issue

        :type issue: Object
        :param issue: the Object representing the issue
        """
        found = None
        flag = True
        i = 0
        while flag and i < GitHubQuerier.ATTEMPTS:
            try:
                found = issue.user
                flag = False
            except:
                time.sleep(GitHubQuerier.WAIT)
                i += 1

        return found

    def get_user_email(self, user):
        """
        gets the email of the issue creator

        :type user: Object
        :param user: the Object representing the user
        """
        found = None
        flag = True
        i = 0
        while flag and i < GitHubQuerier.ATTEMPTS:
            try:
                found = user.email
                flag = False
            except:
                time.sleep(GitHubQuerier.WAIT)
                i += 1

        return found

    def get_pull_request_commit_info(self, commit):
        """
        gets the information of a commit

        :type commit: Object
        :param commit: the Object representing the commit
        """
        found = None
        flag = True
        i = 0
        while flag and i < GitHubQuerier.ATTEMPTS:
            try:
                self._token_util.wait_is_usable(self._github)
                found = commit.commit
                flag = False
            except:
                time.sleep(GitHubQuerier.WAIT)
                i += 1

        return found

    def get_pull_request_commit_stats(self, commit):
        """
        gets the stats (deletions, additions) of a commit

        :type commit: Object
        :param commit: the Object representing the commit
        """
        found = None
        flag = True
        i = 0
        while flag and i < GitHubQuerier.ATTEMPTS:
            try:
                self._token_util.wait_is_usable(self._github)
                found = commit.stats
                flag = False
            except:
                time.sleep(GitHubQuerier.WAIT)
                i += 1

        return found

    def get_user_name(self, user):
        """
        gets the user name of the issue creator

        :type user: Object
        :param user: the Object representing the user
        """
        try:
            found = user.login
        except:
            found = None

        return found

    def get_issue_tags(self, issue):
        """
        gets labels of the issue

        :type issue: Object
        :param issue: the Object representing the issue
        """
        fetched = []
        labels = []
        flag = True
        i = 0
        while flag and i < GitHubQuerier.ATTEMPTS:
            try:
                self._token_util.wait_is_usable(self._github)
                fetched = issue.get_labels()
                flag = False
            except:
                time.sleep(GitHubQuerier.WAIT)
                i += 1

        for label in fetched:
            labels.append(label.name)

        return labels

    def get_pull_request_commits(self, pr):
        """
        gets the commits of a pull request

        :type pr: Object
        :param pr: the Object representing the pull request
        """
        commits = []
        flag = True
        i = 0
        while flag and i < GitHubQuerier.ATTEMPTS:
            try:
                self._token_util.wait_is_usable(self._github)
                commits = pr.get_commits()
                flag = False
            except:
                time.sleep(GitHubQuerier.WAIT)
                i += 1

        return commits

    def get_pull_request_comments(self, pr):
        """
        gets the comments of a pull request

        :type pr: Object
        :param pr: the Object representing the pull request
        """
        comments = []
        flag = True
        i = 0
        while flag and i < GitHubQuerier.ATTEMPTS:
            try:
                self._token_util.wait_is_usable(self._github)
                comments = pr.get_review_comments()
                flag = False
            except:
                time.sleep(GitHubQuerier.WAIT)
                i += 1

        return comments

    def get_pull_request_author(self, pr):
        """
        gets pull request author

        :type pr: Object
        :param pr: the Object representing the pull request
        """
        found = None
        flag = True
        i = 0
        while flag and i < GitHubQuerier.ATTEMPTS:
            try:
                self._token_util.wait_is_usable(self._github)
                found = pr.user
                flag = False
            except:
                time.sleep(GitHubQuerier.WAIT)
                i += 1

        return found

    def get_pull_request_merged_at(self, pr):
        """
        gets the date of a pull request merge

        :type pr: Object
        :param pr: the Object representing the pull request
        """
        found = None
        flag = True
        i = 0
        while flag and i < GitHubQuerier.ATTEMPTS:
            try:
                self._token_util.wait_is_usable(self._github)
                found = pr.merged_at
                flag = False
            except:
                time.sleep(GitHubQuerier.WAIT)
                i += 1

        return found

    def get_pull_request_merged_by(self, pr):
        """
        gets the author of a pull request merge

        :type pr: Object
        :param pr: the Object representing the pull request
        """
        found = None
        flag = True
        i = 0
        while flag and i < GitHubQuerier.ATTEMPTS:
            try:
                self._token_util.wait_is_usable(self._github)
                found = pr.merged_by
                flag = False
            except:
                time.sleep(GitHubQuerier.WAIT)
                i += 1

        return found

    def get_pull_request_files(self, pr):
        """
        gets the files of a pull request

        :type pr: Object
        :param pr: the Object representing the pull request
        """
        files = []
        flag = True
        i = 0
        while flag and i < GitHubQuerier.ATTEMPTS:
            try:
                self._token_util.wait_is_usable(self._github)
                files = pr.get_files()
                flag = False
            except:
                time.sleep(GitHubQuerier.WAIT)
                i += 1

        return files

    def get_issue_comments(self, issue):
        """
        gets the comments of the issue

        :type issue: Object
        :param issue: the Object representing the issue
        """
        comments = []
        flag = True
        i = 0
        while flag and i < GitHubQuerier.ATTEMPTS:
            try:
                self._token_util.wait_is_usable(self._github)
                comments = issue.get_comments()
                flag = False
            except:
                time.sleep(GitHubQuerier.WAIT)
                i += 1

        return comments

    def get_issue_comment_id(self, issue_comment):
        """
        gets the id of the issue comment

        :type issue_comment: Object
        :param issue_comment: the Object representing the issue comment
        """
        found = None
        flag = True
        i = 0
        while flag and i < GitHubQuerier.ATTEMPTS:
            try:
                self._token_util.wait_is_usable(self._github)
                found = issue_comment.id
                flag = False
            except:
                time.sleep(GitHubQuerier.WAIT)
                i += 1

        return found

    def get_issue_comment_body(self, issue_comment):
        """
        gets the body of the issue comment

        :type issue_comment: Object
        :param issue_comment: the Object representing the issue comment
        """
        found = None
        flag = True
        i = 0
        while flag and i < GitHubQuerier.ATTEMPTS:
            try:
                self._token_util.wait_is_usable(self._github)
                found = issue_comment.body
                flag = False
            except:
                time.sleep(GitHubQuerier.WAIT)
                i += 1

        return found

    def get_issue_comment_author(self, issue_comment):
        """
        gets the author of the issue comment

        :type issue_comment: Object
        :param issue_comment: the Object representing the issue comment
        """
        found = None
        flag = True
        i = 0
        while flag and i < GitHubQuerier.ATTEMPTS:
            try:
                self._token_util.wait_is_usable(self._github)
                found = issue_comment.user
                flag = False
            except:
                time.sleep(GitHubQuerier.WAIT)
                i += 1

        return found

    def get_issue_comment_creation_time(self, issue_comment):
        """
        gets the creation time of the issue comment

        :type issue_comment: Object
        :param issue_comment: the Object representing the issue comment
        """
        found = None
        flag = True
        i = 0
        while flag and i < GitHubQuerier.ATTEMPTS:
            try:
                self._token_util.wait_is_usable(self._github)
                found = issue_comment.created_at
                flag = False
            except:
                time.sleep(GitHubQuerier.WAIT)
                i += 1

        return found

    def get_pull_request_commented_file(self, pr_comment):
        """
        gets the file referred by the pull request comment

        :type issue_comment: Object
        :param issue_comment: the Object representing the pull request comment
        """
        found = None
        flag = True
        i = 0
        while flag and i < GitHubQuerier.ATTEMPTS:
            try:
                self._token_util.wait_is_usable(self._github)
                found = pr_comment.path
                flag = False
            except:
                time.sleep(GitHubQuerier.WAIT)
                i += 1

        return found

    def generate_attachment_id(self, message_id, pos):
        """
        creates the attachment id

        :type message_id: int
        :param message_id: the data source message id

        :type pos: int
        :param pos: position of the message
        """
        return str(message_id) + str(pos)

    def get_attachments(self, comment):
        """
        gets the attachements within a comment

        :type comment: str
        :param comment: content of the comment
        """
        p = re.compile("\[.*\]\(http.*\)", re.MULTILINE)
        matches = p.findall(comment)

        attachments = []
        for m in matches:
            attachments.append(m)
        return attachments

    def get_attachment_name(self, text):
        """
        gets the name of the attachement

        :type text: str
        :param text: content of the comment
        """
        parts = text.split('](')
        name = parts[0].lstrip('[')

        found = name

        if not found:
            found = parts[1].split('/')[-1]

        return found

    def get_attachment_url(self, text):
        """
        gets the URL of the attachement

        :type text: str
        :param text: content of the comment
        """
        parts = text.split('](')
        return parts[1].rstrip(')')

    def get_referenced_issues(self, comment):
        """
        gets the referenced issues within a comment

        :type comment: str
        :param comment: content of the comment
        """
        p = re.compile('#\d+', re.MULTILINE)

        matches = p.findall(comment)

        referenced_issues = []
        for m in matches:
            referenced_issues.append(m.strip('#'))

        return referenced_issues

    def get_event_creation_time(self, event):
        """
        gets the creation time of an event

        :type event: Object
        :param event: the Object representing the event
        """
        fetched = None
        flag = True
        i = 0
        while flag and i < GitHubQuerier.ATTEMPTS:
            try:
                fetched = event.created_at
                flag = False
            except:
                time.sleep(GitHubQuerier.WAIT)
                i += 1

        return fetched

    def get_event_actor(self, event):
        """
        gets the actor of an event

        :type event: Object
        :param event: the Object representing the event
        """
        fetched = None
        flag = True
        i = 0
        while flag and i < GitHubQuerier.ATTEMPTS:
            try:
                fetched = event.actor
                flag = False
            except:
                time.sleep(GitHubQuerier.WAIT)
                i += 1

        return fetched

    def get_issue_history(self, issue):
        """
        gets the event history of an issue

        :type issue: Object
        :param issue: the Object representing the issue
        """
        events = []
        flag = True
        i = 0
        while flag and i < GitHubQuerier.ATTEMPTS:
            try:
                self._token_util.wait_is_usable(self._github)
                events = issue.get_events()
                flag = False
            except:
                time.sleep(GitHubQuerier.WAIT)
                i += 1

        return events

    def regenerate_token(self):
        """
        regenerate GitHub token
        """
        self._github = Github(self._token)

    def find_user(self, login):
        """
        finds GitHub user

        :type login: str
        :param login: GitHub username
        """
        found = None
        flag = True
        i = 0
        while flag and i < GitHubQuerier.ATTEMPTS:
            try:
                self._token_util.wait_is_usable(self._github)
                users = self._github.search_users(login, **{"type": "user", "in": "login"})
                flag = False
                for user in users:
                    found = user
                    break
            except:
                time.sleep(GitHubQuerier.WAIT)
                i += 1

        return found

    def get_issue_subscribers(self, history):
        """
        gets subscribers of an issue

        :type history: Object
        :param history: the Object representing the events of an issue
        """
        subscribers = []
        for event in history:
            if event.event == "subscribed":
                subscribers.append(event.actor)
        return subscribers

    def get_issue_assignees(self, history):
        """
        gets assignees of an issue

        :type history: Object
        :param history: the Object representing the events of an issue
        """
        assignees = []
        for event in history:
            if event.event in ["assigned", "unassigned"]:
                if event.event == "assigned":
                    assignees.append(event._rawData.get('assignee'))
                elif event.event == "unassigned":
                    assignees.remove(event._rawData.get('assignee'))
        return assignees

    def get_commit_dependencies(self, history):
        """
        gets dependencies between an issue and commits

        :type history: Object
        :param history: the Object representing the events of an issue
        """
        commit_dependencies = []
        for event in history:
            if event.event == "referenced":
                commit_dependencies.append(event.commit_id)
        return commit_dependencies

    def get_author_by_commit(self, sha):
        found = None
        flag = True
        i = 0
        while flag and i < GitHubQuerier.ATTEMPTS:
            try:
                self._token_util.wait_is_usable(self._github)
                found = self._repo.get_commit(sha).author
                flag = False
            except:
                time.sleep(GitHubQuerier.WAIT)
                i += 1

        return found

    def get_committer_by_commit(self, sha):
        found = None
        flag = True
        i = 0
        while flag and i < GitHubQuerier.ATTEMPTS:
            try:
                self._token_util.wait_is_usable(self._github)
                found = self._repo.get_commit(sha).committer
                flag = False
            except:
                time.sleep(GitHubQuerier.WAIT)
                i += 1

        return found
