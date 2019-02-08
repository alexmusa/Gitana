#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

from util.db_util import DbUtil


class GitHubDao():
    """
    This class handles the persistence and retrieval of GitHub issue tracker data
    """

    def __init__(self, config, logger):
        """
        :type config: dict
        :param config: the DB configuration file

        :type logger: Object
        :param logger: logger
        """
        try:
            self._config = config
            self._logger = logger
            self._db_util = DbUtil()
            self._cnx = self._db_util.get_connection(self._config)
        except:
            self._logger.error("GitHubDao init failed", exc_info=True)
            raise

    def select_issue_tracker_id(self, repo_id, issue_tracker_name):
        """
        gets DB issue tracker id by its name

        :type repo_id: int
        :param repo_id: id of the repository associated to the issue tracker

        :type issue_tracker_name: str
        :param issue_tracker_name: issue tracker name
        """
        return self._db_util.select_issue_tracker_id(self._cnx, issue_tracker_name, self._logger)

    def insert_issue_comment(self, own_id, position, type, issue_id, body, votes, author_id, created_at):
        """
        inserts issue comment

        :type own_id: id
        :param own_id: data source message id

        :type position: int
        :param position: position of the comment

        :type type: str
        :param type: type of the message

        :type issue_id: id
        :param issue_id: DB issue id

        :type body: str
        :param body: body of the comment

        :type votes: int
        :param votes: votes of the comment

        :type author_id: int
        :param author_id: id of the author

        :type created_at: str
        :param created_at: creation date of the comment
        """
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO message " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        arguments = [None, own_id, position, type, issue_id, 0, 0, 0, body, votes, author_id, created_at]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def select_proposed_commit_id(self, sha, repo_id):
        """
        selects id of a proposed commit by its SHA

        :type sha: str
        :param sha: SHA of the commit

        :type repo_id: int
        :param repo_id: id of the repository
        """
        found = None
        cursor = self._cnx.cursor()
        query = "SELECT id " \
                "FROM proposed_commit " \
                "WHERE sha = %s AND repo_id = %s"
        arguments = [sha, repo_id]
        cursor.execute(query, arguments)
        row = cursor.fetchone()

        if row:
            found = row[0]

        cursor.close()
        return found

    def insert_proposed_commit(self, repo_id, sha, message, author_id, committer_id, authored_date, committed_date):
        """
        inserts a proposed commit to DB

        :type repo_id: int
        :param repo_id: id of the repository

        :type sha: str
        :param sha: SHA of the commit

        :type message: str
        :param message: message of the commit

        :type author_id: int
        :param author_id: author id of the commit

        :type committer_id: int
        :param committer_id: committer id of the commit

        :type authored_date: str
        :param authored_date: authored date of the commit

        :type committed_date: str
        :param committed_date: committed date of the commit
        """
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO proposed_commit " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        arguments = [None, repo_id, sha, message.strip(), author_id, committer_id, authored_date, committed_date]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def insert_pull_request_commit(self, pull_request_id, commit_id, proposed_commit_id):
        """
        inserts matched pull request commit to DB

        :type pull_request_id: int
        :param pull_request_id: pull request DB id

        :type commit_id: int
        :param commit_id: id of the commit stored in Gitana

        :type proposed_commit_id: int
        :param proposed_commit_id: id of the commit that was proposed for merge
        """
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO pull_request_commit " \
                "VALUES (%s, %s, %s)"
        arguments = [pull_request_id, commit_id, proposed_commit_id]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def insert_pull_request_review(self, comment_id, pr_id, file_id, proposed_file_id):
        """
        inserts dependency between pull request comment and a file id

        :type comment_id: int
        :param comment_id: id of the comment

        :type pr_id: int
        :param pr_id: id of the pull request

        :type file_id: id
        :param file_id: DB file id

        :type proposed_file_id: id
        :param proposed_file_id: DB proposed file id
        """
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO pull_request_review " \
                "VALUES (%s, %s, %s, %s)"
        arguments = [comment_id, pr_id, file_id, proposed_file_id]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def select_pull_request_comment_id(self, own_id, pr_id):
        """
        gets pull request comment id

        :type own_id: id
        :param own_id: data source message id
        """
        cursor = self._cnx.cursor()
        query = "SELECT id FROM message WHERE own_id = %s AND pull_request_id = %s"
        arguments = [str(own_id), pr_id]
        cursor.execute(query, arguments)
        row = cursor.fetchone()
        found = None
        if row:
            found = row[0]
        cursor.close()

        return found

    def insert_pull_request_comment(self, own_id, position, type, pr_id, body, votes, author_id, created_at):
        """
        inserts pull request comment

        :type own_id: id
        :param own_id: data source message id

        :type position: int
        :param position: position of the comment

        :type type: str
        :param type: type of the message

        :type pr_id: id
        :param pr_id: DB pull request id

        :type body: str
        :param body: body of the comment

        :type votes: int
        :param votes: votes of the comment

        :type author_id: int
        :param author_id: id of the author

        :type created_at: str
        :param created_at: creation date of the comment
        """
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO message " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        arguments = [None, own_id, position, type, 0, 0, 0, pr_id, body, votes, author_id, created_at]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def select_event_type(self, name):
        """
        selects event type id by its name

        :type name: str
        :param name: name of the event
        """
        cursor = self._cnx.cursor()
        query = "SELECT id FROM issue_event_type WHERE name = %s"
        arguments = [name]
        cursor.execute(query, arguments)
        row = cursor.fetchone()
        found = None
        if row:
            found = row[0]
        cursor.close()

        return found

    def insert_issue_event(self, issue_id, event_type_id, detail, creator_id, created_at, target_user_id):
        """
        inserts issue event

        :type issue_id: int
        :param issue_id: DB issue id

        :type event_type_id: int
        :param event_type_id: event type id

        :type detail: str
        :param detail: detail of the event

        :type creator_id: int
        :param creator_id: id of the creator

        :type created_at: str
        :param created_at: creation date of the event

        :type target_user_id: int
        :param target_user_id: target user id
        """
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO issue_event " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s)"
        arguments = [None, issue_id, event_type_id, detail, creator_id, created_at, target_user_id]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def insert_issue_commit_dependency(self, issue_id, commit_id):
        """
        inserts dependency between commit and issue

        :type issue_id: int
        :param issue_id: DB issue id

        :type commit_id: int
        :param commit_id: DB commit id
        """
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO issue_commit_dependency " \
                "VALUES (%s, %s)"
        arguments = [issue_id, commit_id]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def insert_event_type(self, name):
        """
        inserts event type

        :type name: str
        :param name: event type name
        """
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO issue_event_type " \
                "VALUES (%s, %s)"
        arguments = [None, name]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def insert_issue_tracker(self, repo_id, issue_tracker_name, type):
        """
        inserts issue tracker

        :type repo_id: int
        :param repo_id: DB repo id

        :type issue_tracker_name: str
        :param issue_tracker_name: issue tracker name

        :type type: str
        :param type: issue tracker type (github, bugzilla, etc.)
        """
        return self._db_util.insert_issue_tracker(self._cnx, repo_id, issue_tracker_name, type, self._logger)

    def get_already_imported_issue_ids(self, issue_tracker_id, repo_id):
        """
        gets issues already stored in DB

        :type issue_tracker_id: int
        :param issue_tracker_id: DB issue tracker id

        :type repo_id: int
        :param repo_id: DB repo id
        """
        issue_ids = []
        cursor = self._cnx.cursor()
        query = "SELECT i.own_id FROM issue i " \
                "JOIN issue_tracker it ON i.issue_tracker_id = it.id " \
                "WHERE issue_tracker_id = %s AND repo_id = %s " \
                "ORDER BY i.id ASC;"
        arguments = [issue_tracker_id, repo_id]
        cursor.execute(query, arguments)
        row = cursor.fetchone()

        while row:
            own_id = int(row[0])
            issue_ids.append(own_id)
            row = cursor.fetchone()

        cursor.close()

        return issue_ids

    def get_pull_request_file_id_by_name(self, file_name, repo_id):
        """
        gets the file id linked to a pull request by name

        :type file_name: str
        :param file_name: name of the file commented

        :type repo_id: int
        :param repo_id: id of the repository
        """
        found = (None, None)
        cursor = self._cnx.cursor()
        query = "SELECT f.id, 'codebase' AS type " \
                "FROM file f " \
                "WHERE f.name = %s AND f.repo_id = %s " \
                "UNION " \
                "SELECT f.id, 'proposed' AS type " \
                "FROM proposed_file f " \
                "WHERE f.name = %s AND f.repo_id = %s"
        arguments = [file_name, repo_id, file_name, repo_id]
        cursor.execute(query, arguments)
        row = cursor.fetchone()

        if row:
            found = (row[0], row[1])

        cursor.close()

        return found

    def get_already_imported_pull_request_ids(self, issue_tracker_id, repo_id):
        """
        gets pull requests already stored in DB

        :type issue_tracker_id: int
        :param issue_tracker_id: DB issue tracker id

        :type repo_id: int
        :param repo_id: DB repo id
        """
        pr_ids = []
        cursor = self._cnx.cursor()
        query = "SELECT i.own_id FROM pull_request pr " \
                "JOIN issue i ON i.id = pr.issue_id " \
                "JOIN issue_tracker it ON i.issue_tracker_id = it.id " \
                "WHERE it.id = %s AND it.repo_id = %s " \
                "ORDER BY i.id ASC;"
        arguments = [issue_tracker_id, repo_id]
        cursor.execute(query, arguments)
        row = cursor.fetchone()

        while row:
            own_id = row[0]
            pr_ids.append(own_id)
            row = cursor.fetchone()

        cursor.close()

        return pr_ids

    def get_message_type_id(self, message_type):
        """
        gets message type id

        :type message_type: str
        :param message_type: message type
        """
        return self._db_util.get_message_type_id(self._cnx, message_type)

    def insert_issue_dependency(self, issue_source_id, issue_target_id, created_at, type):
        """
        inserts dependency between issues

        :type issue_source_id: int
        :param issue_source_id: issue source id

        :type issue_target_id: int
        :param issue_target_id: issue target id

        :type created_at: str
        :param created_at: date of the dependency creation

        :type type: str
        :param type: type of dependency
        """
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO issue_dependency " \
                "VALUES (%s, %s, %s, %s)"
        arguments = [issue_source_id, issue_target_id, created_at, type]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def select_project_id(self, project_name):
        """
        selects project id by its name

        :type project_name: str
        :param project_name: name of a project
        """
        return self._db_util.select_project_id(self._cnx, project_name, self._logger)

    def select_issue_own_id(self, issue_id, issue_tracker_id, repo_id):
        """
        selects data source issue id

        :type issue_id: int
        :param issue_id: DB issue id

        :type issue_tracker_id: int
        :param issue_tracker_id: issue tracker id

        :type repo_id: int
        :param repo_id: repository id
        """
        found = None
        cursor = self._cnx.cursor()
        query = "SELECT i.own_id " \
                "FROM issue i JOIN issue_tracker it ON i.issue_tracker_id = it.id " \
                "WHERE i.id = %s AND issue_tracker_id = %s AND repo_id = %s"
        arguments = [issue_id, issue_tracker_id, repo_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()

        if row:
            found = int(row[0])

        cursor.close()
        return found

    def get_issue_dependency_type_id(self, name):
        """
        get id of the issue dependency type

        :type name: str
        :param name: name of the dependency type
        """
        return self._db_util.get_issue_dependency_type_id(self._cnx, name)

    def select_commit(self, sha, repo_id):
        """
        gets commit by its SHA

        :type sha: str
        :param sha: SHA of the commit

        :type repo_id: int
        :param repo_id: repository id
        """
        found = None
        cursor = self._cnx.cursor()
        query = "SELECT id " \
                "FROM commit " \
                "WHERE sha = %s AND repo_id = %s"
        arguments = [sha, repo_id]
        cursor.execute(query, arguments)
        row = cursor.fetchone()

        if row:
            found = row[0]

        cursor.close()
        return found

    def select_issue_id(self, issue_own_id, issue_tracker_id, repo_id):
        """
        gets issue id

        :type issue_own_id: int
        :param issue_own_id: data source issue id

        :type issue_tracker_id: int
        :param issue_tracker_id: issue tracker id

        :type repo_id: int
        :param repo_id: repository id
        """
        found = None
        cursor = self._cnx.cursor()
        query = "SELECT i.id FROM issue i " \
                "JOIN issue_tracker it ON i.issue_tracker_id = it.id " \
                "WHERE own_id = %s AND issue_tracker_id = %s AND repo_id = %s"
        arguments = [issue_own_id, issue_tracker_id, repo_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()

        if row:
            found = row[0]

        cursor.close()
        return found

    def select_pull_request_id(self, pr_own_id, issue_tracker_id):
        """
        gets pull request id

        :type pr_own_id: int
        :param pr_own_id: data source pull request id

        :type issue_tracker_id: int
        :param issue_tracker_id: issue tracker id
        """
        found = None
        cursor = self._cnx.cursor()
        query = "SELECT pr.id FROM pull_request pr JOIN issue i ON pr.issue_id = i.id " \
                "WHERE i.own_id = %s AND i.issue_tracker_id = %s"
        arguments = [pr_own_id, issue_tracker_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()

        if row:
            found = row[0]

        cursor.close()
        return found

    def update_issue(self, issue_id, issue_tracker_id, summary, component, version, hardware, priority, severity, reference_id, last_change_at):
        """
        updates an issue

        :type issue_id: int
        :param issue_id: data source issue id

        :type issue_tracker_id: int
        :param issue_tracker_id: issue tracker id

        :type summary: str
        :param summary: new issue description

        :type component: str
        :param component: component where the issue was found

        :type version: str
        :param version: version where the issue was found

        :type hardware: str
        :param hardware: hardware where the issue was found

        :type priority: str
        :param priority: priority of the issue

        :type severity: str
        :param severity: severity of the issue

        :type reference_id: int
        :param reference_id: id of the Git reference where the issue was found

        :type last_change_at: str
        :param last_change_at: last change date of the issue
        """
        cursor = self._cnx.cursor()
        query = "UPDATE issue SET last_change_at = %s, summary = %s, component = %s, version = %s, hardware = %s, priority = %s, severity = %s, reference_id = %s WHERE own_id = %s AND issue_tracker_id = %s"
        arguments = [last_change_at, summary, component, version, hardware, priority, severity, reference_id, issue_id, issue_tracker_id]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def update_pull_request(self, pr_own_id, issue_tracker_id, summary, status, merged, last_change_at):
        """
        updates a pull request

        :type pr_own_id: int
        :param pr_own_id: data source pr id

        :type issue_tracker_id: int
        :param issue_tracker_id: issue tracker id

        :type summary: str
        :param summary: new pull request description

        :type status: str
        :param status: new pull request status

        :type merged: bool
        :param merged: new pull request merged status

        :type last_change_at: str
        :param last_change_at: last change date of the issue
        """
        cursor = self._cnx.cursor()
        query = "UPDATE pull_request SET last_change_at = %s, summary = %s, status = %s, merged = %s WHERE own_id = %s AND issue_tracker_id = %s"
        arguments = [last_change_at, summary, status, merged, pr_own_id, issue_tracker_id]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def insert_issue(self, issue_own_id, issue_tracker_id, summary, component, version, hardware, priority, severity, reference_id, user_id, created_at, last_change_at):
        """
        inserts an issue

        :type issue_own_id: int
        :param issue_own_id: data source issue id

        :type issue_tracker_id: int
        :param issue_tracker_id: issue tracker id

        :type summary: str
        :param summary: new issue description

        :type component: str
        :param component: component where the issue was found

        :type version: str
        :param version: version where the issue was found

        :type hardware: str
        :param hardware: hardware where the issue was found

        :type priority: str
        :param priority: priority of the issue

        :type severity: str
        :param severity: severity of the issue

        :type reference_id: int
        :param reference_id: id of the Git reference where the issue was found

        :type user_id: int
        :param user_id: issue creator id

        :type created_at: str
        :param created_at: creation date of the issue

        :type last_change_at: str
        :param last_change_at: last change date of the issue
        """
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO issue " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        arguments = [None, issue_own_id, issue_tracker_id, summary, component, version, hardware, priority, severity, reference_id, user_id, created_at, last_change_at]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def insert_pull_request(self, pr_own_id, author_id, state, target_ref_id, merged_at, merged_by, issue_tracker_id, repo_id):
        """
        inserts a pull request (note that the pull request id is equal to the issue id,
        since that in GitHub every pull request is an issue

        :type pr_own_id: int
        :param pr_own_id: data source pull request id

        :type author_id: int
        :param author_id: author id

        :type state: str
        :param state: pull request state

        :type target_ref_id: int
        :param target_ref_id: target reference

        :type merged_at: timestamp
        :param merged_at: pull request merged time

        :type merged_by: int
        :param merged_by: merger id
        """
        cursor = self._cnx.cursor()
        issue_id = self.select_issue_id(pr_own_id, issue_tracker_id, repo_id)
        query = "INSERT IGNORE INTO pull_request " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s)"
        arguments = [None, issue_id, author_id, state, target_ref_id, merged_at, merged_by]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def select_proposed_file_id(self, repo_id, name):
        """
        selects id of the proposed file

        :type repo_id: int
        :param repo_id: id of the repository

        :type name: str
        :param name: name of the file (full path)
        """
        cursor = self._cnx.cursor()
        query = "SELECT id " \
                "FROM proposed_file " \
                "WHERE name = %s AND repo_id = %s"
        arguments = [name, repo_id]
        cursor.execute(query, arguments)
        try:
            id = cursor.fetchone()[0]
        except:
            id = None
        cursor.close()
        return id

    def insert_proposed_file(self, repo_id, filename, ext):
        """
        inserts file not part of the codebase proposed in a pull request

        :type repo_id: int
        :param repo_id: id of the repository

        :type filename: str
        :param filename: name of the file

        :type ext: str
        :param ext: extension of the file
        """
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO proposed_file " \
                "VALUES (%s, %s, %s, %s)"
        arguments = [None, repo_id, filename, ext]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def insert_proposed_file_modification(self, proposed_commit_id, file_id, proposed_file_id, status, additions, deletions, changes, patch_content):
        """
        inserts a proposed file modification to DB

        :type proposed_commit_id: int
        :param proposed_commit_id: id of the proposed commit

        :type file_id: int
        :param file_id: id of the file

        :type proposed_file_id: int
        :param proposed_file_id: id of the proposed file

        :type status: str
        :param status: type of the modification

        :type additions: int
        :param additions: number of additions

        :type deletions: int
        :param deletions: number of deletions

        :type changes: int
        :param changes: number of changes

        :type patch_content: str
        :param patch_content: content of the patch
        """
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO proposed_file_modification " \
                "VALUES (NULL, %s, %s, %s, %s, %s, %s, %s, %s)"
        arguments = [proposed_commit_id, file_id, proposed_file_id, status, additions, deletions, changes, patch_content]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def insert_label(self, name):
        """
        inserts a label

        :type name: str
        :param name: the name of the label
        """
        self._db_util.insert_label(self._cnx, name, self._logger)

    def select_label_id(self, name):
        """
        selects the label id by its name

        :type name: str
        :param name: the name of the label
        """
        return self._db_util.select_label_id(self._cnx, name, self._logger)

    def select_issue_comment_id(self, own_id, issue_id, created_at):
        """
        selects the id of an issue comment

        :type own_id: int
        :param own_id: data source comment id

        :type issue_id: int
        :param issue_id: DB issue id

        :type created_at: str
        :param created_at: creation date of the issue
        """
        cursor = self._cnx.cursor()
        query = "SELECT id FROM message WHERE own_id = %s AND issue_id = %s AND created_at = %s"
        arguments = [own_id, issue_id, created_at]
        cursor.execute(query, arguments)
        row = cursor.fetchone()
        found = None
        if row:
            found = row[0]
        cursor.close()

        return found

    def get_user_id(self, user_name, user_email):
        """
        selects the id of a user

        :type user_name: str
        :param user_name: name of the user

        :type user_email: str
        :param user_email: email of the user
        """

        if user_email == None and user_name == None:
            user_name = "unknown_user"
            user_email = "unknown_user"

        if user_name:
            user_id = self._db_util.select_user_id_by_name(self._cnx, user_name, self._logger)
        else:
            user_id = self._db_util.select_user_id_by_email(self._cnx, user_email, self._logger)

        if not user_id:
            self._db_util.insert_user(self._cnx, user_name, user_email, self._logger)
            if user_email:
                user_id = self._db_util.select_user_id_by_email(self._cnx, user_email, self._logger)
            else:
                user_id = self._db_util.select_user_id_by_name(self._cnx, user_name, self._logger)

        return user_id

    def insert_subscriber(self, issue_id, subscriber_id):
        """
        inserts issue subscriber

        :type issue_id: int
        :param issue_id: db issue id

        :type subscriber_id: int
        :param subscriber_id: subscriber id
        """
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO issue_subscriber " \
                "VALUES (%s, %s)"
        arguments = [issue_id, subscriber_id]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def insert_assignee(self, issue_id, assignee_id):
        """
        inserts issue assignee

        :type issue_id: int
        :param issue_id: db issue id

        :type assignee_id: int
        :param assignee_id: assignee id
        """
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO issue_assignee " \
                "VALUES (%s, %s)"
        arguments = [issue_id, assignee_id]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def insert_attachment(self, attachment_id, issue_comment_id, name, url):
        """
        inserts attachment

        :type attachment_id: int
        :param attachment_id: db attachment id

        :type issue_comment_id: int
        :param issue_comment_id: issue comment id

        :type name: str
        :param name: name of the attachment

        :type url: str
        :param url: url of the attachment
        """
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO attachment " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s)"
        arguments = [None, attachment_id, issue_comment_id, name, None, None, url]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def assign_label_to_issue(self, issue_id, label_id):
        """
        links label to issue

        :type issue_id: int
        :param issue_id: db issue id

        :type label_id: int
        :param label_id: label id
        """
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO issue_labelled " \
                "VALUES (%s, %s)"
        arguments = [issue_id, label_id]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def find_reference_id(self, version, issue_id, repo_id):
        """
        retrieves reference id

        :type version: str
        :param version: name of the reference

        :type issue_id: int
        :param issue_id: db issue id

        :type repo_id: int
        :param repo_id: repository id
        """
        found = None
        if version:
            try:
                cursor = self._cnx.cursor()
                query = "SELECT id FROM reference WHERE name = %s AND repo_id = %s"
                arguments = [version, repo_id]
                cursor.execute(query, arguments)
                row = cursor.fetchone()
                if row:
                    found = row[0]
                else:
                    #sometimes the version is followed by extra information such as alpha, beta, RC, M.
                    query = "SELECT id FROM reference WHERE name LIKE '" + str(version) + "%' AND repo_id = " + str(repo_id)
                    cursor.execute(query)
                    row = cursor.fetchone()

                    if row:
                        found = row[0]

                cursor.close()
            except Exception:
                self._logger.warning("version (" + str(version) + ") not inserted for issue id: " + str(issue_id), exc_info=True)

        return found

    def select_last_change_issue(self, issue_id, issue_tracker_id, repo_id):
        """
        retrieves last change date of an issue

        :type issue_id: int
        :param issue_id: db issue id

        :type issue_tracker_id: int
        :param issue_tracker_id: issue tracker id

        :type repo_id: int
        :param repo_id: repository id
        """
        found = None

        cursor = self._cnx.cursor()
        query = "SELECT i.last_change_at " \
                "FROM issue i JOIN issue_tracker it ON i.issue_tracker_id = it.id " \
                "WHERE own_id = %s AND issue_tracker_id = %s AND repo_id = %s"
        arguments = [issue_id, issue_tracker_id, repo_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()

        if row:
            found = row[0]

        cursor.close()
        return found

    def select_last_change_pull_request(self, pr_id, issue_tracker_id, repo_id):
        """
        retrieves last change date of a pull request

        :type pr_id: int
        :param pr_id: db pull request id

        :type issue_tracker_id: int
        :param issue_tracker_id: issue tracker id

        :type repo_id: int
        :param repo_id: repository id
        """
        found = None

        cursor = self._cnx.cursor()
        query = "SELECT pr.last_change_at " \
                "FROM pull_request pr JOIN issue_tracker it ON pr.issue_tracker_id = it.id " \
                "WHERE own_id = %s AND issue_tracker_id = %s AND repo_id = %s"
        arguments = [pr_id, issue_tracker_id, repo_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()

        if row:
            found = row[0]

        cursor.close()
        return found

    def select_repo_id(self, project_id, repo_name):
        """
        selects repository id

        :type project_id: int
        :param project_id: project id

        :type repo_name: int
        :param repo_name: repository name
        """
        return self._db_util.select_repo_id(self._cnx, repo_name, self._logger)

    def get_cursor(self):
        return self._cnx.cursor()

    def close_cursor(self, cursor):
        return cursor.close()

    def fetchone(self, cursor):
        return cursor.fetchone()

    def execute(self, cursor, query, arguments):
        cursor.execute(query, arguments)

    def close_connection(self):
        if self._cnx:
            self._db_util.close_connection(self._cnx)

    def restart_connection(self):
        self._cnx = self._db_util.restart_connection(self._config, self._logger)