#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

from util.db_util import DbUtil


class GitDao():
    """
    This class handles the persistence and retrieval of Git data
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
            self._logger.error("GitDao init failed")
            raise

    def check_connection_alive(self):
        try:
            cursor = self._cnx.cursor()
            cursor.execute("SELECT VERSION()")
            results = cursor.fetchone()
            ver = results[0]
            cursor.close()
            if not ver:
                self._cnx = self._db_util.restart_connection(self._config, self._logger)
        except:
            self._cnx = self._db_util.restart_connection(self._config, self._logger)

    def close_connection(self):
        self._db_util.close_connection(self._cnx)

    def restart_connection(self):
        self._cnx = self._db_util.restart_connection(self._config, self._logger)

    def get_connection(self):
        return self._cnx

    def get_cursor(self):
        return self._cnx.cursor()

    def close_cursor(self, cursor):
        return cursor.close()

    def fetchone(self, cursor):
        return cursor.fetchone()

    def execute(self, cursor, query, arguments):
        cursor.execute(query, arguments)

    def array2string(self, array):
        return ','.join(str(x) for x in array)

    def function_at_commit_is_empty(self, repo_id):
        """
        checks function at commit table is empty

        :type repo_id: int
        :param repo_id: id of an existing repository in the DB
        """
        cursor = self._cnx.cursor()
        query = "SELECT COUNT(*) " \
                "FROM commit c " \
                "JOIN function_at_commit fac ON c.id = fac.commit_id " \
                "WHERE c.repo_id = %s"
        arguments = [repo_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()
        count = 0
        if row:
            count = int(row[0])

        cursor.close()

        return int(count > 0)

    def select_code_at_commit(self, commit_id, file_id):
        """
        retrieve the code at commit info for a given file and commit

        :type commit_id: int
        :param commit_id: id of an existing commit in the DB

        :type file_id: int
        :param file_id: id of an existing file in the DB
        """
        found = None
        cursor = self._cnx.cursor()
        query = "SELECT * " \
                "FROM code_at_commit " \
                "WHERE commit_id = %s AND file_id = %s"
        arguments = [commit_id, file_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()
        if row:
            found = row

        cursor.close()

        return found

    def line_detail_table_is_empty(self, repo_id):
        """
        checks line detail table is empty

        :type repo_id: int
        :param repo_id: id of an existing repository in the DB
        """
        cursor = self._cnx.cursor()
        query = "SELECT COUNT(*) " \
                "FROM commit c " \
                "JOIN file_modification fm ON c.id = fm.commit_id " \
                "JOIN line_detail l ON fm.id = l.file_modification_id " \
                "WHERE l.content IS NOT NULL AND repo_id = %s"
        arguments = [repo_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()
        count = 0
        if row:
            count = int(row[0])

        cursor.close()

        return int(count > 0)

    def code_at_commit_is_empty(self, repo_id):
        """
        checks code at commit table is empty

        :type repo_id: int
        :param repo_id: id of an existing repository in the DB
        """
        cursor = self._cnx.cursor()
        query = "SELECT COUNT(*) " \
                "FROM commit c " \
                "JOIN code_at_commit cac ON c.id = cac.commit_id " \
                "WHERE c.repo_id = %s"
        arguments = [repo_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()
        count = 0
        if row:
            count = int(row[0])

        cursor.close()

        return int(count > 0)

    def file_modification_patch_is_empty(self, repo_id):
        """
        checks patch column in file modification table is empty

        :type repo_id: int
        :param repo_id: id of an existing repository in the DB
        """
        cursor = self._cnx.cursor()
        query = "SELECT COUNT(*) " \
                "FROM commit c " \
                "JOIN file_modification fm ON c.id = fm.commit_id " \
                "WHERE patch IS NOT NULL and repo_id = %s"
        arguments = [repo_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()
        count = 0
        if row:
            count = int(row[0])

        cursor.close()

        return int(count > 0)

    def get_last_commit_id(self, repo_id):
        """
        gets last commit id

        :type repo_id: int
        :param repo_id: id of an existing repository in the DB
        """
        found = None
        cursor = self._cnx.cursor()
        query = "SELECT MAX(id) as last_commit_id " \
                "FROM commit c " \
                "WHERE repo_id = %s"
        arguments = [repo_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()
        if row:
            found = row[0]

        cursor.close()
        return found

    def select_repo_id(self, repo_name):
        """
        selects id of a repository by its name

        :type repo_name: str
        :param repo_name: name of an existing repository in the DB
        """
        return self._db_util.select_repo_id(self._cnx, repo_name, self._logger)

    def insert_repo(self, project_id, repo_name):
        """
        inserts repository to DB

        :type project_id: int
        :param project_id: id of an existing project in the DB

        :type repo_name: str
        :param repo_name: name of a repository to insert
        """
        return self._db_util.insert_repo(self._cnx, project_id, repo_name, self._logger)

    def select_project_id(self, project_name):
        """
        selects id of a project by its name

        :type project_name: str
        :param project_name: name of an existing project in the DB
        """
        return self._db_util.select_project_id(self._cnx, project_name, self._logger)

    def get_user_id(self, user_name, user_email):
        """
        gets id of a user

        :type user_name: str
        :param user_name: name of the user

        :type user_email: str
        :param user_email: email of the user
        """

        if user_email == None and user_name == None:
            user_name = "unknown_user"
            user_email = "unknown_user"

        if user_email:
            user_id = self._db_util.select_user_id_by_email(self._cnx, user_email, self._logger)
        else:
            user_id = self._db_util.select_user_id_by_name(self._cnx, user_name, self._logger)

        if not user_id:
            self._db_util.insert_user(self._cnx, user_name, user_email, self._logger)
            user_id = self._db_util.select_user_id_by_email(self._cnx, user_email, self._logger)

        return user_id

    def insert_commit_parents(self, parents, commit_id, sha, repo_id):
        """
        inserts commit parents to DB, one by one

        :type parents: list of Object
        :param parents: parents of a commit

        :type commit_id: int
        :param commit_id: id of the commit

        :type sha: str
        :param sha: SHA of the commit

        :type repo_id: int
        :param repo_id: id of the repository
        """
        cursor = self._cnx.cursor()
        for parent in parents:
            parent_id = self.select_commit_id(parent.hexsha, repo_id)

            if not parent_id:
                self._logger.warning("parent commit id not found! SHA parent " + str(parent.hexsha))

            query = "INSERT IGNORE INTO commit_parent " \
                    "VALUES (%s, %s, %s, %s, %s)"

            if parent_id:
                arguments = [repo_id, commit_id, sha, parent_id, parent.hexsha]
            else:
                arguments = [repo_id, commit_id, sha, None, parent.hexsha]

            cursor.execute(query, arguments)
            self._cnx.commit()

        cursor.close()

    def insert_all_commit_parents(self, parents, commit_id, sha, repo_id):
        """
        inserts commit parents to DB all together

        :type parents: list of Object
        :param parents: parents of a commit

        :type commit_id: int
        :param commit_id: id of the commit

        :type sha: str
        :param sha: SHA of the commit

        :type repo_id: int
        :param repo_id: id of the repository
        """
        to_insert = []
        for parent in parents:
            parent_id = self.select_commit_id(parent.hexsha, repo_id)

            if not parent_id:
                self._logger.warning("parent commit id not found! SHA parent " + str(parent.hexsha))

            if parent_id:
                to_insert.append((repo_id, commit_id, sha, parent_id, parent.hexsha))
            else:
                to_insert.append((repo_id, commit_id, sha, None, parent.hexsha))

        if to_insert:
            cursor = self._cnx.cursor()
            query = "INSERT IGNORE INTO commit_parent(repo_id, commit_id, commit_sha, parent_id, parent_sha) VALUES (%s, %s, %s, %s, %s)"
            cursor.executemany(query, [i for i in to_insert])
            self._cnx.commit()
            cursor.close()

    def insert_commits_in_reference(self, commits_data):
        """
        inserts commits to DB all together

        :type commits_data: list of Object
        :param commits_data: commit data
        """
        if commits_data:
            cursor = self._cnx.cursor()
            query = "INSERT IGNORE INTO commit_in_reference(repo_id, commit_id, ref_id) VALUES (%s, %s, %s)"
            cursor.executemany(query, commits_data)
            self._cnx.commit()
            cursor.close()

    def insert_commit_in_reference(self, repo_id, commit_id, ref_id):
        """
        inserts commit to DB

        :type repo_id: int
        :param repo_id: id of the repository

        :type commit_id: int
        :param commit_id: id of the commit

        :type ref_id: int
        :param ref_id: id of the reference
        """
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO commit_in_reference " \
                "VALUES (%s, %s, %s)"
        arguments = [repo_id, commit_id, ref_id]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def insert_line_details(self, file_modification_id, detail):
        """
        inserts line details to DB

        :type file_modification_id: int
        :param file_modification_id: id of the file modification

        :type detail: str
        :param detail: line content
        """
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO line_detail " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s)"

        arguments = [file_modification_id, detail[0], detail[1], detail[2], detail[3], detail[4], detail[5]]

        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def select_file_modification_id(self, commit_id, file_id):
        """
        selects file modification id

        :type commit_id: int
        :param commit_id: id of the commit

        :type file_id: int
        :param file_id: id of the file
        """
        cursor = self._cnx.cursor()
        query = "SELECT id " \
                "FROM file_modification " \
                "WHERE commit_id = %s AND file_id = %s"
        arguments = [commit_id, file_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()
        found = None
        if row:
            found = row[0]

        cursor.close()
        return found

    def insert_file_modification(self, commit_id, file_id, status, additions, deletions, changes, patch_content):
        """
        inserts file modification to DB

        :type commit_id: int
        :param commit_id: id of the commit

        :type file_id: int
        :param file_id: id of the file

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
        query = "INSERT IGNORE INTO file_modification " \
                "VALUES (NULL, %s, %s, %s, %s, %s, %s, %s)"
        arguments = [commit_id, file_id, status, additions, deletions, changes, patch_content]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def insert_file_renamed(self, repo_id, current_file_id, previous_file_id, file_modification_id):
        """
        inserts file renamed information

        :type repo_id: int
        :param repo_id: id of the repository

        :type current_file_id: int
        :param current_file_id: id of the renamed file

        :type previous_file_id: int
        :param previous_file_id: id of the file before renaming

        :type file_modification_id: int
        :param file_modification_id: id of the file modification
        """
        cursor = self._cnx.cursor()

        query = "INSERT IGNORE INTO file_renamed " \
                "VALUES (%s, %s, %s, %s)"
        arguments = [repo_id, current_file_id, previous_file_id, file_modification_id]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def insert_file(self, repo_id, name, ext):
        """
        inserts file

        :type repo_id: int
        :param repo_id: id of the repository

        :type name: str
        :param name: name of the file (full path)

        :type ext: str
        :param ext: extension of the file
        """
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO file " \
                "VALUES (%s, %s, %s, %s)"
        arguments = [None, repo_id, name, ext]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def select_file_id(self, repo_id, name):
        """
        selects id of the file

        :type repo_id: int
        :param repo_id: id of the repository

        :type name: str
        :param name: name of the file (full path)
        """
        cursor = self._cnx.cursor()
        query = "SELECT id " \
                "FROM file " \
                "WHERE name = %s AND repo_id = %s"
        arguments = [name, repo_id]
        cursor.execute(query, arguments)
        try:
            id = cursor.fetchone()[0]
        except:
            id = None
        cursor.close()
        return id

    def insert_reference(self, repo_id, ref_name, ref_type):
        """
        inserts reference

        :type repo_id: int
        :param repo_id: id of the repository

        :type ref_name: str
        :param ref_name: name of the reference

        :type ref_type: str
        :param ref_type: type of the reference (branch or tag)
        """
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO reference " \
                "VALUES (%s, %s, %s, %s)"
        arguments = [None, repo_id, ref_name, ref_type]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def select_reference_name(self, repo_id, ref_id):
        """
        selects reference name by its id

        :type repo_id: int
        :param repo_id: id of the repository

        :type ref_id: int
        :param ref_id: id of the reference
        """
        found = None
        cursor = self._cnx.cursor()
        query = "SELECT name " \
                "FROM reference " \
                "WHERE id = %s and repo_id = %s"
        arguments = [ref_id, repo_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()

        if row:
            found = row[0]

        cursor.close()

        return found

    def select_reference_id(self, repo_id, ref_name):
        """
        selects reference id by its name

        :type repo_id: int
        :param repo_id: id of the repository

        :type ref_name: str
        :param ref_name: name of the reference
        """
        found = None
        cursor = self._cnx.cursor()
        query = "SELECT id " \
                "FROM reference " \
                "WHERE name = %s and repo_id = %s"
        arguments = [ref_name, repo_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()
        if row:
            found = row[0]

        cursor.close()
        return found

    def insert_commit(self, repo_id, sha, message, author_id, committer_id, authored_date, committed_date, size):
        """
        inserts commit to DB

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

        :type size: int
        :param size: size of the commit
        """
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO commit " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        arguments = [None, repo_id, sha, message.strip(), author_id, committer_id, authored_date, committed_date, size]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def select_function_id(self, file_id, start_line, end_line):
        """
        select DB function id

        :type file_id: int
        :param file_id: id of the file

        :type start_line: int
        :param start_line: line number where the function starts

        :type end_line: int
        :param end_line: line number where the function ends
        """
        found = None
        cursor = self._cnx.cursor()
        query = "SELECT id " \
                "FROM function " \
                "WHERE file_id = %s AND start_line = %s AND end_line = %s"
        arguments = [file_id, start_line, end_line]
        cursor.execute(query, arguments)

        row = cursor.fetchone()

        if row:
            found = row[0]

        cursor.close()

        return found

    def insert_code_at_commit(self, commit_id, file_id, ccn, loc, comments, blanks, funs, tokens, avg_ccn, avg_loc, avg_tokens):
        """
        inserts to DB code information of a file at a given commit

        :type commit_id: int
        :param commit_id: id of the commit

        :type file_id: int
        :param file_id: id of the file

        :type ccn: int
        :param ccn: cyclomatic complexity value

        :type loc: int
        :param loc: lines of code

        :type comments: int
        :param comments: commented lines

        :type blanks: int
        :param blanks: blank lines

        :type funs: int
        :param funs: number of functions

        :type tokens: int
        :param tokens: tokens in the files

        :type avg_ccn: int
        :param avg_ccn: file avg cyclomatic complexity (per function)

        :type avg_loc: int
        :param avg_loc: file avg lines of code (per function)

        :type avg_tokens: int
        :param avg_tokens: file avg number of tokens (per function)
        """
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO code_at_commit " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        arguments = [commit_id, file_id, ccn, loc, comments, blanks, funs, tokens, avg_ccn, avg_loc, avg_tokens]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def insert_function(self, function_name, file_id, num_arguments, loc, tokens, total_lines, ccn, start_line, end_line):
        """
        inserts function to DB

        :type function_name: str
        :param function_name: name of the function

        :type file_id: int
        :param file_id: id of the file

        :type num_arguments: int
        :param num_arguments: number of arguments

        :type loc: int
        :param loc: lines of code

        :type tokens: int
        :param tokens: tokens in the function

        :type total_lines: int
        :param total_lines: number of lines (loc + comments + empty lines)

        :type ccn: int
        :param ccn: cyclomatic complexity of the function

        :type start_line: int
        :param start_line: line number where the function starts

        :type end_line: int
        :param end_line: line number where the function ends
        """
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO function " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        arguments = [None, function_name, file_id, num_arguments, loc, tokens, total_lines, ccn, start_line, end_line]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def insert_function_at_commit(self, fun_id,  commit_id):
        """
        inserts link between a function and the commit

        :type fun_id: int
        :param fun_id: id of the function

        :type commit_id: int
        :param commit_id: id of the commit
        """
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO function_at_commit " \
                "VALUES (%s, %s)"
        arguments = [commit_id, fun_id]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def update_commit_parent(self, parent_id, parent_sha, repo_id):
        """
        inserts commit parent to DB

        :type parent_id: int
        :param parent_id: id of the commit parent

        :type parent_sha: str
        :param parent_sha: SHA of the commit parent

        :type repo_id: int
        :param repo_id: id of the repository
        """
        cursor = self._cnx.cursor()
        query_update = "UPDATE commit_parent " \
                       "SET parent_id = %s " \
                       "WHERE parent_id IS NULL AND parent_sha = %s AND repo_id = %s "
        arguments = [parent_id, parent_sha, repo_id]
        cursor.execute(query_update, arguments)
        self._cnx.commit()
        cursor.close()

    def fix_commit_parent_table(self, repo_id):
        """
        checks for missing commit parent information and fixes it

        :type repo_id: int
        :param repo_id: id of the repository
        """
        cursor = self._cnx.cursor()
        query_select = "SELECT parent_sha " \
                       "FROM commit_parent " \
                       "WHERE parent_id IS NULL AND repo_id = %s"
        arguments = [repo_id]
        cursor.execute(query_select, arguments)
        row = cursor.fetchone()
        while row:
            parent_sha = row[0]
            parent_id = self.select_commit_id(parent_sha, repo_id)
            self.update_commit_parent(parent_id, parent_sha, repo_id)
            row = cursor.fetchone()
        cursor.close()

    def select_commit_id(self, sha, repo_id):
        """
        selects id of a commit by its SHA

        :type sha: str
        :param sha: SHA of the commit

        :type repo_id: int
        :param repo_id: id of the repository
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

    def select_all_developer_ids(self, repo_id):
        """
        selects all developers (committers or authors) of a given repo

        :type repo_id: int
        :param repo_id: id of the repository
        """
        user_ids = []
        cursor = self._cnx.cursor()
        query = "SELECT c.author_id " \
                "FROM commit c JOIN repository r ON c.repo_id = r.id JOIN user u ON u.id = c.author_id " \
                "WHERE repo_id = %s " \
                "UNION " \
                "SELECT c.committer_id " \
                "FROM commit c JOIN repository r ON c.repo_id = r.id JOIN user u ON u.id = c.committer_id " \
                "WHERE repo_id = %s "
        arguments = [repo_id, repo_id]
        cursor.execute(query, arguments)
        row = cursor.fetchone()

        while row:
            user_id = row[0]
            user_ids.append(user_id)
            row = cursor.fetchone()

        cursor.close()
        return user_ids

    def select_sha_commit_by_user(self, user_id, repo_id, match_on="author"):
        """
        selects the SHA of the first commit (authored or committed) by a given user id

        :type user_id: int
        :param user_id: id of the user

        :type repo_id: int
        :param repo_id: id of the repository

        :type match_on: str (author or committer)
        :param match_on: define whether to perform the match on the author id or committer id
        """
        found = None
        cursor = self._cnx.cursor()

        if match_on == "committer":
            query = "SELECT sha " \
                    "FROM commit " \
                    "WHERE committer_id = %s AND repo_id = %s " \
                    "LIMIT 1"
        else:
            query = "SELECT sha " \
                    "FROM commit " \
                    "WHERE author_id = %s AND repo_id = %s " \
                    "LIMIT 1"
        arguments = [user_id, repo_id]
        cursor.execute(query, arguments)
        row = cursor.fetchone()

        if row:
            found = row[0]

        return found

    def select_file_changes(self, file_id, ref_id, before_date=None, patch=False, code=False):
        """
        get all file changes, excluding renamings for a given file within a reference

        :type file_id: int
        :param file_id: id of the file

        :type ref_id: int
        :param ref_id: id of the reference

        :type before_date: str
        :param before_date: if not null, it retrieves the changes before the given date

        :type patch: bool
        :param: patch: if True, it retrieves also the patch associate to each file change

        :type code: bool
        :param: code: if True, it retrieves also code-related information of the file (ccn, loc, commented lines, etc.)
        """
        found = []

        before_date_selection = ""
        if before_date:
            before_date_selection = " AND c.authored_date <= '" + str(before_date) + "'"

        patch_selection = ", NULL AS patch"
        if patch:
            patch_selection = ", fm.patch"

        code_selection = ""
        code_join = ""
        if code:
            code_selection = ", " \
                             "IFNULL(cac.ccn, 0) AS ccn, " \
                             "IFNULL(cac.loc, 0) AS loc, " \
                             "IFNULL(cac.commented_lines, 0) AS commented_lines, " \
                             "IFNULL(cac.blank_lines, 0) AS blank_lines, " \
                             "IFNULL(cac.funs, 0) AS funs, " \
                             "IFNULL(cac.tokens, 0) AS tokens, " \
                             "IFNULL(cac.avg_ccn, 0) AS avg_ccn, " \
                             "IFNULL(cac.avg_loc, 0) AS avg_loc, " \
                             "IFNULL(cac.avg_tokens, 0) AS avg_tokens"
            code_join = "LEFT JOIN code_at_commit cac ON cac.commit_id = c.id AND cac.file_id = f.id "

        cursor = self._cnx.cursor()
        query = "SELECT f.id, f.name, c.sha, c.message, IFNULL(ua.alias_id, c.author_id) AS author_id, " \
                "c.authored_date, c.committed_date, fm.status, fm.additions, fm.deletions, " \
                "fm.changes" + patch_selection + code_selection + " " \
                "FROM file f join file_modification fm on f.id = fm.file_id " \
                "JOIN commit c ON c.id = fm.commit_id " \
                "JOIN commit_in_reference cin ON cin.commit_id = c.id " \
                "JOIN reference r ON r.id = cin.ref_id " \
                "LEFT JOIN user_alias ua ON ua.user_id = c.author_id " + code_join + " " \
                "WHERE f.id = %s and r.id = %s" + before_date_selection
        arguments = [file_id, ref_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()

        while row:
            file_id = row[0]
            file_name = row[1]
            sha = row[2]
            message = row[3]
            author_id = int(row[4])

            authored_date = row[5]
            committed_date = row[6]
            status = str(row[7])
            additions = int(row[8])
            deletions = int(row[9])
            changes = int(row[10])

            git_data = {'sha': sha,
                        'commit_message': message,
                        'author_id': author_id,
                        'authored_date': authored_date,
                        'committed_date': committed_date,
                        'status': status,
                        'additions': additions,
                        'deletions': deletions,
                        'changes': changes,
                        'file_name': file_name,
                        'file_id': file_id}

            patch_data = {}
            if patch:
                patch = str(row[11])
                patch_data = {'patch': patch}


            code_data = {}
            if code:
                ccn = int(row[12])
                loc = int(row[13])
                commented_lines = int(row[14])
                blank_lines = int(row[15])
                funs = int(row[16])
                tokens = int(row[17])
                avg_ccn = float(row[18])
                avg_loc = float(row[19])
                avg_tokens = float(row[20])

                code_data = {'ccn': ccn,
                             'loc': loc,
                             'commented_lines': commented_lines,
                             'blank_lines': blank_lines,
                             'funs': funs,
                             'tokens': tokens,
                             'avg_ccn': avg_ccn,
                             'avg_loc': avg_loc,
                             'avg_tokens': avg_tokens}

            found.append(dict(git_data.items() + patch_data.items() + code_data.items()))
            row = cursor.fetchone()

        cursor.close()

        return found

    def select_file_renamings(self, file_id, ref_id):
        """
        get file renamings for a given file within a reference

        :type file_id: int
        :param file_id: id of the file

        :type ref_id: int
        :param ref_id: id of the reference
        """
        renamings = []
        cursor = self._cnx.cursor()
        query = "SELECT fr.current_file_id, fr.previous_file_id, c.authored_date, c.authored_date, c.committed_date " \
                "FROM file f JOIN file_modification fm ON f.id = fm.file_id " \
                "JOIN commit c ON c.id = fm.commit_id " \
                "JOIN commit_in_reference cin ON cin.commit_id = c.id " \
                "JOIN reference r ON r.id = cin.ref_id " \
                "JOIN file_renamed fr ON fr.file_modification_id = fm.id AND fr.current_file_id = f.id " \
                "WHERE f.id = %s and r.id = %s AND fm.status = 'renamed';"
        arguments = [file_id, ref_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()

        while row:
            renamings.append(row[1])
            row = cursor.fetchone()

        cursor.close()

        if len(renamings) > 1:
            self._logger.warning("The file with id " + str(file_id) + " has multiple renamings in reference " + str(ref_id) + "!")

        return renamings
