__author__ = 'valerio cosentino'

from util.date_util import DateUtil
from util.db_util import DbUtil
from util.file_util import FileUtil
from util.logging_util import LoggingUtil
import simplejson as json
import re
import codecs
from datetime import datetime


class FileJsonExporter:
    """
    This class handles the export of file information via JSON. It allows to use a former version of
    the bus factor tool (https://github.com/SOM-Research/busfactor)
    """

    LOG_FOLDER_PATH = "logs"

    def __init__(self, config, db_name, log_root_path):
        """
        :type config: dict
        :param config: the DB configuration file

        :type db_name: str
        :param config: name of an existing DB

        :type log_root_path: str
        :param log_root_path: the log path
        """
        self._date_util = DateUtil()
        self._db_util = DbUtil()

        self._logging_util = LoggingUtil()
        self._log_path = log_root_path + "export-file-json-" + db_name
        self._logger = self._logging_util.get_logger(self._log_path)
        self._fileHandler = self._logging_util.get_file_handler(self._logger, self._log_path, "info")

        self._db_name = db_name
        config.update({'database': db_name})
        self._config = config

        self._cnx = self._db_util.get_connection(self._config)
        self._db_util.set_database(self._cnx, self._db_name)
        self._db_util.set_settings(self._cnx)
        self._file_util = FileUtil(self._config, self._logger)

    def get_diff_info(self, patch_content):
        if patch_content:
            first_line = patch_content.split('\n')[0]
            if re.match(r"^@@(\s|\+|\-|\d|,)+@@", first_line, re.M):
                diff_info = first_line.split("@@")[1]
            else:
                diff_info = "Binary file"
        else:
            diff_info = 'Renamed file'

        return diff_info

    def get_diff_content(self, patch_content):
        if patch_content:
            lines = patch_content.split('\n')
            if re.match(r"^@@(\s|\+|\-|\d|,)+@@", lines[0], re.M):
                first_line_content = lines[0].split("@@")[2]
                diff_content = lines[1:]
                diff_content.insert(0, first_line_content)
                diff_content = '\n'.join(diff_content)
            else:
                diff_content = "No content"
        else:
            diff_content = "No content"

        return diff_content

    def get_patch_info(self, content):
        diff_info = self.get_diff_info(content)
        diff_content = self.get_diff_content(content)
        return {'info': diff_info, 'content': diff_content.decode('utf-8', 'ignore')}

    def get_changes_for_file(self, file_ids):
        file_modifications = []
        cursor = self._cnx.cursor()
        query = "SELECT c.author_id, c.committer_id, c.authored_date, c.committed_date, c.sha, fm.additions, fm.deletions, fm.patch " \
                "FROM file_modification fm JOIN file f ON fm.file_id = f.id  " \
                "JOIN commit_in_reference cin ON cin.commit_id = fm.commit_id " \
                "JOIN reference r ON r.id = cin.ref_id " \
                "JOIN commit c ON c.id = cin.commit_id " \
                "WHERE f.id IN (" + ",".join([str(id) for id in file_ids]) + ") " \
                "ORDER BY c.authored_date DESC"
        cursor.execute(query)
        row = cursor.fetchone()

        while row:
            author_id = row[0]
            committer_id = row[1]
            authored_date = row[2].strftime('%Y-%m-%d %H:%M:%S')
            committed_date = row[3].strftime('%Y-%m-%d %H:%M:%S')
            additions = str(row[4])
            deletions = str(row[5])
            sha = str(row[6])
            patch = str(row[7])

            patch_info = self.get_patch_info(patch)

            author_name, author_email = self.get_user_identity(author_id)

            if author_id != committer_id:
                committer_name, committer_email = self.get_user_identity(committer_id)
            else:
                committer_name = author_name
                committer_email = author_email

            author = {'name': author_name, 'email': author_email}
            committer = {'name': committer_name, 'email': committer_email}

            file_modifications.append({'author': author,
                                       'authored_date': authored_date,
                                       'committer': committer,
                                       'committed_date': committed_date,
                                       'additions': additions,
                                       'deletions': deletions,
                                       'sha': sha,
                                       'patch': patch_info})

            row = cursor.fetchone()
        cursor.close()

        return file_modifications

    def array2string(self, array):
        return ','.join(str(x) for x in array)

    def get_user_identity(self, user_id):
        found = None

        cursor = self._cnx.cursor()
        query = "SELECT u.name, u.email " \
                "FROM user u " \
                "JOIN (SELECT IFNULL(ua.alias_id, u.id) as user_id FROM user u LEFT JOIN user_alias ua ON u.id = ua.user_id WHERE u.id = %s) as aliased " \
                "ON aliased.user_id = u.id"
        arguments = [user_id]
        cursor.execute(query, arguments)
        row = cursor.fetchone()

        if row:
            name = row[0]
            email = row[1]
            found = (name, email)

        return found

    def get_commits_info(self, file_ids):
        commits = []
        cursor = self._cnx.cursor()
        query = "SELECT c.sha, c.message, r.name, c.author_id, c.committer_id, c.authored_date, c.committed_date " \
                "FROM file_modification fm JOIN file f ON fm.file_id = f.id " \
                "JOIN commit_in_reference cin ON cin.commit_id = fm.commit_id " \
                "JOIN reference r ON r.id = cin.ref_id " \
                "JOIN commit c ON c.id = cin.commit_id " \
                "WHERE f.id IN (" + ",".join([str(id) for id in file_ids]) + ")"
        cursor.execute(query)
        row = cursor.fetchone()
        while row:
            sha = str(row[0])
            message = str(row[1].encode('utf8'))
            ref = str(row[2])
            author_id = row[3]
            committer_id = row[4]
            authored_date = row[5].strftime('%Y-%m-%d %H:%M:%S')
            committed_date = row[6].strftime('%Y-%m-%d %H:%M:%S')

            author_name, author_email = self.get_user_identity(author_id)

            if author_id != committer_id:
                committer_name, committer_email = self.get_user_identity(committer_id)
            else:
                committer_name = author_name
                committer_email = author_email

            author = {'name': author_name, 'email': author_email}
            committer = {'name': committer_name, 'email': committer_email}
            commits.append({'sha': sha,
                            'author': author,
                            'committer': committer,
                            'message': message,
                            'ref': ref,
                            'authored_date': authored_date,
                            'committed_date': committed_date})
            row = cursor.fetchone()
        cursor.close()

        return commits

    def get_status_file(self, file_id):
        cursor = self._cnx.cursor()
        query = "SELECT fm.status, MAX(c.committed_date) AS last_modification " \
                "FROM file_modification fm JOIN file f ON fm.file_id = f.id " \
                "JOIN commit_in_reference cin ON cin.commit_id = fm.commit_id " \
                "JOIN commit c ON c.id = cin.commit_id " \
                "WHERE f.id = %s"
        arguments = [file_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()
        cursor.close()

        status = ""
        last_modification = ""
        if row:
            status = row[0]
            last_modification = row[1].strftime('%Y-%m-%d %H:%M:%S')

        return {'status': status, 'last_modification': last_modification}

    def add_file_info_to_json(self, references, repo_json):
        cursor = self._cnx.cursor()
        query = "SELECT f.id, f.name, f.ext, r.name, r.id " \
                "FROM repository repo JOIN commit_in_reference cin ON repo.id = cin.repo_id " \
                "JOIN file_modification fm ON fm.commit_id = cin.commit_id " \
                "JOIN file f ON f.id = fm.file_id " \
                "JOIN reference r ON r.id = cin.ref_id " \
                "WHERE repo.id = %s AND r.name IN (" + ",".join(["'" + ref + "'" for ref in references]) + ") AND " \
                "f.id NOT IN " \
                            "(SELECT deletions.file_id FROM " \
                                        "(SELECT fm.file_id, c.committed_date " \
                                        "FROM commit_in_reference cin " \
                                        "JOIN file_modification fm ON fm.commit_id = cin.commit_id  " \
                                        "JOIN reference r ON r.id = cin.ref_id " \
                                        "JOIN commit c ON c.id = fm.commit_id " \
                                        "WHERE fm.status = 'deleted' AND cin.repo_id = %s ) as deletions " \
                                        "JOIN " \
                                        "(SELECT fm.file_id, max(c.committed_date) as committed_date " \
                                        "FROM commit_in_reference cin " \
                                        "JOIN file_modification fm ON fm.commit_id = cin.commit_id " \
                                        "JOIN reference r ON r.id = cin.ref_id " \
                                        "JOIN commit c ON c.id = fm.commit_id " \
                                        "WHERE fm.status <> 'deleted' AND cin.repo_id = %s " \
                                        "GROUP BY fm.file_id) AS last_action " \
                                        "ON deletions.file_id = last_action.file_id " \
                                        "WHERE deletions.committed_date > last_action.committed_date " \
                                        "UNION " \
                                        "SELECT fr.previous_file_id " \
                                        "FROM file_renamed fr JOIN file f ON fr.previous_file_id = f.id " \
                                        "JOIN file_modification fm ON fm.file_id = f.id " \
                                        "JOIN commit_in_reference cin ON cin.commit_id = fm.commit_id " \
                                        "JOIN reference r ON r.id = cin.ref_id " \
                                        "WHERE cin.repo_id = %s) " \
                "GROUP BY f.id, r.id"
        arguments = [self._repo_id, self._repo_id, self._repo_id, self._repo_id]
        cursor.execute(query, arguments)
        row = cursor.fetchone()
        while row:
            file_id = row[0]
            file_name = row[1]
            file_ext = row[2]
            ref_name = row[3]
            ref_id = row[4]

            status = self.get_status_file(file_id)
            file_history = self._file_util.get_file_history_by_id(file_id, ref_id)
            file_ids = list(set([h.get("file_id") for h in file_history]))

            commits = self.get_commits_info(file_ids)
            directories = self._file_util.get_directories(file_name)
            changes_info = self.get_changes_for_file(file_ids)

            file_info = {'repo': self._repo_name,
                         'info': status,
                         'commits': commits,
                         'ref': ref_name,
                         'id': str(file_id),
                         'name': file_name.split('/')[-1],
                         'ext': file_ext,
                         'dirs': directories,
                         'file_changes': changes_info}
            repo_json.write(json.dumps(file_info) + "\n")
            row = cursor.fetchone()
        cursor.close()

    def export(self, repo_name, references, file_path):
        """
        exports the file data to JSON format

        :type repo_name: str
        :param repo_name: name of the repository to analyse

        :type references: list str
        :param references: list of references to analyse

        :type file_path: str
        :param file_path: the path where to export the file information
        """
        try:
            self._logger.info("FileJSONExporter started")
            start_time = datetime.now()

            repo_json = codecs.open(file_path, 'w', "utf-8")
            self._repo_name = repo_name
            self._repo_id = self._db_util.select_repo_id(self._cnx, repo_name, self._logger)
            self.add_file_info_to_json(references, repo_json)
            repo_json.close()

            self._db_util.close_connection(self._cnx)

            end_time = datetime.now()
            minutes_and_seconds = self._logging_util.calculate_execution_time(end_time, start_time)
            self._logger.info("FileJSONExporter: process finished after " + str(minutes_and_seconds[0])
                             + " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
            self._logging_util.remove_file_handler_logger(self._logger, self._fileHandler)
        except:
            self._logger.error("FileJSONExporter failed", exc_info=True)