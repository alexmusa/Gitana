#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

import mysql.connector
from mysql.connector import errorcode


class DbUtil():
    """
    This class provides database utilities
    """

    def get_connection(self, config):
        """
        gets DB connection

        :type config: dict
        :param config: the DB configuration file
        """
        return mysql.connector.connect(**config)

    def close_connection(self, cnx):
        """
        closes DB connection

        :type cnx: Object
        :param cnx: DB connection to close
        """
        cnx.close()

    def lowercase(self, _str):
        """
        conver str to lowercase

        :type _str: str
        :param _str: str to convert
        """
        if _str:
            _str = _str.lower()

        return _str

    def select_project_id(self, cnx, project_name, logger=None):
        """
        gets project id

        :type cnx: Object
        :param cnx: DB connection

        :type project_name: str
        :param project_name: name of the project

        :type logger: Object
        :param logger: logger
        """
        found = None
        cursor = cnx.cursor()
        query = "SELECT p.id " \
                "FROM project p " \
                "WHERE p.name = %s"
        arguments = [project_name]
        cursor.execute(query, arguments)
        row = cursor.fetchone()

        if row:
            found = row[0]
        else:
            if logger:
                logger.error("the project " + str(project_name) + " does not exist")

        cursor.close()
        return found

    def insert_project(self, cnx, db_name, project_name):
        """
        inserts a project in the DB

        :type cnx: Object
        :param cnx: DB connection

        :type db_name: str
        :param db_name: the name of an existing DB

        :type project_name: str
        :param project_name: the name of the project to create
        """
        self.set_database(cnx, db_name)
        cursor = cnx.cursor()
        query = "INSERT IGNORE INTO project " \
                "VALUES (%s, %s)"
        arguments = [None, project_name]
        cursor.execute(query, arguments)
        cnx.commit()
        cursor.close()

    def insert_repo(self, cnx, project_id, repo_name, logger=None):
        """
        inserts repository

        :type cnx: Object
        :param cnx: DB connection

        :type project_id: int
        :param project_id: id of the project

        :type repo_name: str
        :param repo_name: name of the repository

        :type logger: Object
        :param logger: logger
        """
        cursor = cnx.cursor()
        query = "INSERT IGNORE INTO repository " \
                "VALUES (%s, %s, %s)"
        arguments = [None, project_id, repo_name]
        cursor.execute(query, arguments)
        cnx.commit()
        cursor.close()

    def insert_issue_tracker(self, cnx, repo_id, issue_tracker_name, issue_type, logger=None):
        """
        inserts issue tracker

        :type cnx: Object
        :param cnx: DB connection

        :type repo_id: int
        :param repo_id: id of the repository

        :type issue_tracker_name: str
        :param issue_tracker_name: name of the issue tracker

        :type issue_type: str
        :param issue_type: type of the issue tracker

        :type logger: Object
        :param logger: logger
        """
        cursor = cnx.cursor()
        query = "INSERT IGNORE INTO issue_tracker " \
                "VALUES (%s, %s, %s, %s)"
        arguments = [None, repo_id, issue_tracker_name, issue_type]
        cursor.execute(query, arguments)
        cnx.commit()

        query = "SELECT id " \
                "FROM issue_tracker " \
                "WHERE name = %s"
        arguments = [issue_tracker_name]
        cursor.execute(query, arguments)

        row = cursor.fetchone()

        if row:
            found = row[0]
        else:
            if logger:
                logger.warning("no issue with name " + str(issue_tracker_name))

        cursor.close()
        return found

    def select_label_id(self, cnx, name, logger=None):
        """
        selects the label id by its name

        :type cnx: Object
        :param cnx: DB connection

        :type name: str
        :param name: the name of the label

        :type logger: Object
        :param logger: logger
        """
        cursor = cnx.cursor()
        query = "SELECT id FROM label WHERE name = %s"
        arguments = [name]
        cursor.execute(query, arguments)
        row = cursor.fetchone()
        found = None

        if row:
            found = row[0]
        else:
            if logger:
                logger.warning("no label with name " + str(name))
        cursor.close()

        return found

    def insert_label(self, cnx, name, logger=None):
        """
        inserts a label

        :type cnx: Object
        :param cnx: DB connection

        :type name: str
        :param name: the name of the label

        :type logger: Object
        :param logger: logger
        """
        cursor = cnx.cursor()
        query = "INSERT IGNORE INTO label " \
                "VALUES (%s, %s)"
        arguments = [None, name]
        cursor.execute(query, arguments)
        cnx.commit()
        cursor.close()

    def select_repo_id(self, cnx, repo_name, logger=None):
        """
        selects repository id

        :type cnx: Object
        :param cnx: DB connection

        :type repo_name: str
        :param repo_name: name of the repository

        :type logger: Object
        :param logger: logger
        """
        found = None
        cursor = cnx.cursor()
        query = "SELECT id " \
                "FROM repository " \
                "WHERE name = %s"
        arguments = [repo_name]
        cursor.execute(query, arguments)

        row = cursor.fetchone()

        if row:
            found = row[0]
        else:
            if logger:
                logger.error("the repository " + repo_name + " does not exist")

        cursor.close()
        return found

    def select_instant_messaging_id(self, cnx, im_name, logger=None):
        """
        selects instant messaging id

        :type cnx: Object
        :param cnx: DB connection

        :type im_name: str
        :param im_name: name of the instant messaging

        :type logger: Object
        :param logger: logger
        """
        found = None
        cursor = cnx.cursor()
        query = "SELECT id " \
                "FROM instant_messaging " \
                "WHERE name = %s"
        arguments = [im_name]
        cursor.execute(query, arguments)

        row = cursor.fetchone()

        if row:
            found = row[0]
        else:
            if logger:
                logger.error("the instant messaging " + im_name + " does not exist")

        cursor.close()
        return found

    def get_all_identities_for_user_by_id(self, cnx, user_id, logger=None):
        """
        gets all identities linked to the user (included the one passed as input)

        :type cnx: Object
        :param cnx: DB connection

        :type user_id: int
        :param user_id: the id of the user

        :type logger: Object
        :param logger: logger
        """
        ids = []
        cursor = cnx.cursor()
        query = "SELECT ua.user_id " \
                "FROM user_alias ua " \
                "WHERE ua.alias_id IN (SELECT user_id FROM user_alias ua WHERE ua.alias_id = %s " \
                                      "UNION SELECT alias_id FROM user_alias ua WHERE ua.user_id = %s)" \
               "UNION " \
               "SELECT ua.alias_id " \
               "FROM user_alias ua " \
               "WHERE ua.alias_id IN (SELECT user_id FROM user_alias ua WHERE ua.alias_id = %s " \
                                     "UNION SELECT alias_id FROM user_alias ua WHERE ua.user_id = %s)"
        arguments = [user_id, user_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()
        while row:
            ids.append(row[0])
            row = cursor.fetchone()

        cursor.close()
        return ids


    def select_all_aliased_user_ids(self, cnx, logger=None):
        """
        selects all aliased user ids

        :type cnx: Object
        :param cnx: DB connection

        :type logger: Object
        :param logger: logger
        """
        alias_ids = []
        cursor = cnx.cursor()

        query = "SELECT alias_id " \
                "FROM user_alias " \
                "UNION " \
                "SELECT user_id " \
                "FROM user_alias"
        cursor.execute(query)

        row = cursor.fetchone()

        while row:
            alias_id = row[0]
            alias_ids.append(alias_id)
            row = cursor.fetchone()

        cursor.close()
        return alias_ids

    def insert_user_alias(self, cnx, name, alias, logger=None):
        """
        inserts user alias

        :type cnx: Object
        :param cnx: DB connection

        :type name: str
        :param name: name of the user

        :type alias: str
        :param alias: alias of the user

        :type logger: Object
        :param logger: logger
        """
        cursor = cnx.cursor()

        query = "INSERT IGNORE INTO user_alias " \
                "VALUES (%s, %s)"
        arguments = [name, alias]
        cursor.execute(query, arguments)
        cnx.commit()
        cursor.close()

    def insert_user(self, cnx, name, email, logger=None):
        """
        inserts user

        :type cnx: Object
        :param cnx: DB connection

        :type name: str
        :param name: name of the user

        :type email: str
        :param email: email of the user

        :type logger: Object
        :param logger: logger
        """
        cursor = cnx.cursor()

        query = "INSERT IGNORE INTO user " \
                "VALUES (%s, %s, %s)"
        arguments = [None, name, email]
        cursor.execute(query, arguments)
        cnx.commit()
        cursor.close()

    def select_file_name_by_id(self, cnx, file_id, logger=None):
        """
        selects the name of the file by its id

        :type cnx: Object
        :param cnx: DB connection

        :type file_id: int
        :param file_id: id of the file

        :type logger: Object
        :param logger: logger
        """
        found = None
        cursor = cnx.cursor()
        query = "SELECT name " \
                "FROM file " \
                "WHERE id = %s"
        arguments = [file_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()

        if row:
            found = str(row[0])
        else:
            if logger:
                logger.warning("there is not file with this id " + str(file_id))

        return found

    def select_user_by_id(self, cnx, id, logger=None):
        """
        selects user by its id

        :type cnx: Object
        :param cnx: DB connection

        :type id: int
        :param id: id of the user

        :type logger: Object
        :param logger: logger
        """
        found = {}
        if id:
            cursor = cnx.cursor()
            query = "SELECT name, email " \
                    "FROM user " \
                    "WHERE id = %s"
            arguments = [id]
            cursor.execute(query, arguments)

            row = cursor.fetchone()

            if row:
                found = {"name": str(row[0]), "email": str(row[1])}
            else:
                if logger:
                    logger.warning("there is not user with this id " + str(id))

            cursor.close()
        return found

    def select_all_user_ids_by_email(self, cnx, email, logger=None):
        """
        selects all user ids by email

        :type cnx: Object
        :param cnx: DB connection

        :type email: str
        :param email: email of the user

        :type logger: Object
        :param logger: logger
        """
        if email:
            found = []
            cursor = cnx.cursor()
            query = "SELECT id " \
                    "FROM user " \
                    "WHERE email = %s"
            arguments = [email]
            cursor.execute(query, arguments)

            row = cursor.fetchone()
            if not row:
                if logger:
                    logger.debug("there is not user with this email " + email)

            while row:
                found.append(row[0])
                row = cursor.fetchone()

            cursor.close()
        return found

    def select_user_id_by_email(self, cnx, email, logger=None):
        """
        selects user id by email

        :type cnx: Object
        :param cnx: DB connection

        :type email: str
        :param email: email of the user

        :type logger: Object
        :param logger: logger
        """
        found = None
        if email:
            cursor = cnx.cursor()
            query = "SELECT id " \
                    "FROM user " \
                    "WHERE email = %s"
            arguments = [email]
            cursor.execute(query, arguments)

            row = cursor.fetchone()

            if row:
                found = row[0]
            else:
                if logger:
                    logger.debug("there is not user with this email " + email)

            cursor.close()
        return found

    def select_user_id_by_name_and_email(self, cnx, name, email, logger=None):
        """
        selects user id by name and email

        :type cnx: Object
        :param cnx: DB connection

        :type name: str
        :param name: name of the user

        :type name: str
        :param name: name of the email

        :type logger: Object
        :param logger: logger
        """
        found = None
        cursor = cnx.cursor()
        query = "SELECT id " \
                "FROM user " \
                "WHERE name = %s AND email = %s"
        arguments = [name, email]
        cursor.execute(query, arguments)

        row = cursor.fetchone()

        if row:
            found = row[0]
        else:
            if logger:
                logger.debug("there is not user with this name, email " + str(name) + "," + str(email))

        cursor.close()
        return found

    def select_all_user_ids_by_name(self, cnx, name, logger=None):
        """
        selects all user ids by name

        :type cnx: Object
        :param cnx: DB connection

        :type name: str
        :param name: name of the user

        :type logger: Object
        :param logger: logger
        """
        if name:
            found = []
            cursor = cnx.cursor()
            query = "SELECT id " \
                    "FROM user " \
                    "WHERE name = %s"
            arguments = [name]
            cursor.execute(query, arguments)

            row = cursor.fetchone()
            if not row:
                if logger:
                    logger.debug("there is not user with this name " + name)

            while row:
                found.append(row[0])
                row = cursor.fetchone()

            cursor.close()
        return found

    def select_user_id_by_name(self, cnx, name, logger=None):
        """
        selects user id by name

        :type cnx: Object
        :param cnx: DB connection

        :type name: str
        :param name: name of the user

        :type logger: Object
        :param logger: logger
        """
        found = None
        if name:
            found = None
            cursor = cnx.cursor()
            query = "SELECT id " \
                    "FROM user " \
                    "WHERE name = %s"
            arguments = [name]
            cursor.execute(query, arguments)

            row = cursor.fetchone()

            if row:
                found = row[0]
            else:
                if logger:
                    logger.debug("there is not user with this name " + name)

            cursor.close()
        return found

    def select_forum_id(self, cnx, forum_name, logger=None):
        """
        selects forum id

        :type cnx: Object
        :param cnx: DB connection

        :type forum_name: str
        :param forum_name: name of the forum

        :type logger: Object
        :param logger: logger
        """
        found = None
        cursor = cnx.cursor()
        query = "SELECT id " \
                "FROM forum " \
                "WHERE name = %s"
        arguments = [forum_name]
        cursor.execute(query, arguments)

        row = cursor.fetchone()

        if row:
            found = row[0]
        else:
            if logger:
                logger.error("the forum " + forum_name + " does not exist")

        cursor.close()
        return found

    def select_issue_tracker_id(self, cnx, issue_tracker_name, logger=None):
        """
        selects issue tracker id

        :type cnx: Object
        :param cnx: DB connection

        :type issue_tracker_name: str
        :param issue_tracker_name: name of the issue tracker

        :type logger: Object
        :param logger: logger
        """
        found = None
        cursor = cnx.cursor()
        query = "SELECT id " \
                "FROM issue_tracker " \
                "WHERE name = %s"
        arguments = [issue_tracker_name]
        cursor.execute(query, arguments)

        row = cursor.fetchone()

        if row:
            found = row[0]
        else:
            if logger:
                logger.error("the issue tracker " + issue_tracker_name + " does not exist")

        cursor.close()
        return found

    def get_issue_dependencies(self, cnx, issue_ids, before_date=None, logger=None):
        """
        selects dependencies for a given set of issues

        :type cnx: Object
        :param cnx: DB connection

        :type issue_ids: list int
        :param issue_ids: list of issue ids

        :type before_date: str
        :param before_date: select dependencies before date (YYYY-mm-dd)

        :type logger: Object
        :param logger: logger
        """
        found = []

        before_condition = ""
        if before_date:
            before_condition = " AND id.created_at < '" + before_date + "'"

        cursor = cnx.cursor()
        query = "SELECT id.issue_source_id " \
                "FROM issue_dependency id " \
                "WHERE id.issue_target_id IN (" + ",".join([str(i) for i in issue_ids]) + ") " + before_condition + " " \
                "GROUP BY id.issue_source_id"
        cursor.execute(query)
        row = cursor.fetchone()

        while row:
            found.append(row[0])
            row = cursor.fetchone()

        cursor.close()
        return found

    def get_issue_dependency_type_id(self, cnx, name, logger=None):
        """
        selects issue dependency type id

        :type cnx: Object
        :param cnx: DB connection

        :type name: str
        :param name: dependency type name

        :type logger: Object
        :param logger: logger
        """
        found = None
        cursor = cnx.cursor()
        query = "SELECT id FROM issue_dependency_type WHERE name = %s"
        arguments = [name]
        cursor.execute(query, arguments)

        row = cursor.fetchone()
        cursor.close()

        if row:
            found = row[0]

        return found

    def get_message_type_id(self, cnx, name, logger=None):
        """
        selects message type id

        :type cnx: Object
        :param cnx: DB connection

        :type name: str
        :param name: message type name

        :type logger: Object
        :param logger: logger
        """

        found = None
        cursor = cnx.cursor()
        query = "SELECT id FROM message_type WHERE name = %s"
        arguments = [name]
        cursor.execute(query, arguments)
        row = cursor.fetchone()

        if row:
            found = row[0]

        cursor.close()
        return found

    def _identify_user_and_alias(self, cnx, original_user, original_alias, logger=None):
        processed = False

        # check that user id and alias id are different. If true, skip the other heuristics
        if original_user == original_alias:
            processed = True

        output = (original_user, original_alias)

        # check that there is no row with user id equal to alias id and viceversa. If true, user id and alias id are inverted to allow the insert ignore to filter it
        if not processed:
            cursor = cnx.cursor()
            check_duplicated_entry = "SELECT ua.user_id, ua.alias_id " \
                                     "FROM user_alias ua " \
                                     "WHERE ua.alias_id = %s AND ua.user_id = %s;"
            arguments = [original_user, original_alias]
            cursor.execute(check_duplicated_entry, arguments)
            row = cursor.fetchone()
            if row:
                output = (original_alias, original_user)
                if logger:
                    logger.info("analysing (user_id: " + str(original_user) + ", alias id: " + str(original_alias) + "). User and alias ids have been already used together, they will not be inserted")
            cursor.close()

        # check that user id is already used as alias in other rows. If true, user id and alias id are inverted
        if not processed:
            cursor = cnx.cursor()
            check_swap_user_with_alias = "SELECT ua.user_id, ua.alias_id " \
                                         "FROM user_alias ua " \
                                         "WHERE (ua.alias_id = %s AND ua.user_id != %s) OR " \
                                         "(ua.user_id = %s AND ua.alias_id != %s)"
            arguments = [original_user, original_alias, original_user, original_alias]
            cursor.execute(check_swap_user_with_alias, arguments)
            row = cursor.fetchone()
            if row:
                existing_alias = row[1]
                output = (original_alias, existing_alias)
                if logger:
                    logger.info("analysing user_id:" + str(original_user) + "alias id: " + str(original_alias) + ". User id is used as alias id in other rows. Alias and user ids are inverted and user id is replaced by the existing alias id")
                processed = True
            cursor.close()

        # check that the alias id is not used as user id in other rows. If true, the alias id is replaced with the existing one
        if not processed:
            cursor = cnx.cursor()
            check_replace_alias = "SELECT alias_id " \
                                  "FROM user_alias ua " \
                                  "WHERE ua.alias_id != %s AND ua.user_id = %s;"
            arguments = [original_user, original_alias]
            cursor.execute(check_replace_alias, arguments)
            row = cursor.fetchone()
            if row:
                existing_alias = row[0]
                output = (original_user, existing_alias)
                if logger:
                    logger.info("analysing user_id:" + str(original_user) + "alias id: " + str(original_alias) + ". Alias id is used as user id in other rows, it will be replaced with the existing one")

            cursor.close()

        return output

    def set_database(self, cnx, db_name, logger=None):
        """
        set database

        :type cnx: Object
        :param cnx: DB connection

        :type db_name: str
        :param db_name: name of the database

        :type logger: Object
        :param logger: logger
        """
        cursor = cnx.cursor()
        use_database = "USE " + db_name
        cursor.execute(use_database)
        cursor.close()

    def set_settings(self, cnx, logger=None):
        """
        set database settings

        :type cnx: Object
        :param cnx: DB connection

        :type logger: Object
        :param logger: logger
        """
        cursor = cnx.cursor()
        cursor.execute("set global innodb_file_format = BARRACUDA")
        cursor.execute("set global innodb_file_format_max = BARRACUDA")
        cursor.execute("set global innodb_large_prefix = ON")
        cursor.execute("set global character_set_server = utf8")
        cursor.execute("set global max_connections = 500")
        cursor.close()

    def restart_connection(self, config, logger=None):
        """
        restart DB connection

        :type config: dict
        :param config: the DB configuration file

        :type logger: Object
        :param logger: logger
        """
        if logger:
            logger.info("restarting connection...")
        return mysql.connector.connect(**config)
