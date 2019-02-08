#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

import lizard
import subprocess
import os
import util
import code2db_extract_commit_file


class CodeQuerier():
    """
    This class collects the code function data using the Lizard python library
    """
    CLOC_PATH = os.path.dirname(util.__file__) + "\cloc\cloc-1.72.exe"
    ALLOWED_EXTENSIONS = ['java', 'py', 'php', 'scala', 'js', 'rb', 'cs', 'cpp', 'c']
    FORBIDDEN_EXTENSIONS = ['tar', 'bz2', "gz", "lz", "apk", "tbz2", "lzma", "tlz", "war", "xar", "zip", "zipx"]

    def __init__(self, logger, tmp_path):
        """
        :type logger: Object
        :param logger: logger

        :type: tmp_path: str
        :param: tmp_path: tmp file path
        """
        try:
            self._logger = logger
            self._tmp_path = tmp_path
        except:
            self._logger.error("FunQuerier init failed")
            raise

    def get_comment_info(self, f):
        info = {'blanks': None, 'comments': None, 'loc': None}
        flag = False
        try:
            with open(self._tmp_path, "w+") as _write:
                pipe = subprocess.Popen([CodeQuerier.CLOC_PATH, f], stdout=_write)
                pipe.communicate()

            with open(self._tmp_path, "r") as _read:
                for line in _read:
                    if flag:
                        if not line.startswith("-----"):
                            digested = " ".join(line.split())
                            info_file = digested.split(" ")
                            blank_lines = int(info_file[2])
                            commented_lines = int(info_file[3])
                            loc = int(info_file[4])
                            info = {'blanks': blank_lines, 'comments': commented_lines, 'loc': loc}
                            break

                    if line.lower().startswith("language"):
                        flag = True
        except Exception:
            self._logger.warning("something went wrong when extracting comment info from " + f, exc_info=True)

        return info

    def get_complexity_info(self, f, import_type):
        funs = []
        i = lizard.analyze_file(f)

        info_comments = self.get_comment_info(f)

        # if i.nloc != info_comments.get('loc'):
        #     self._logger.warning("CLOC and Lizard report different LOC : " + str(i.nloc) + " (Lizard) "
        #                        + str(info_comments.get('loc')) + " (CLOC)")

        overall = {'ccn': i.CCN,
                   'avg_ccn': i.average_cyclomatic_complexity,
                   'avg_loc': i.average_nloc,
                   'avg_tokens': i.average_token_count,
                   'funs': len(i.function_list),
                   'loc': i.nloc,
                   'tokens': i.token_count,
                   'comments': info_comments.get('comments'),
                   'blanks': info_comments.get('blanks')
                   }

        if import_type == code2db_extract_commit_file.Code2DbCommitFile.FULL_IMPORT_TYPE:
            for fun in i.function_list:
                funs.append(
                    {'ccn': fun.cyclomatic_complexity,
                     'tokens': fun.token_count,
                     'loc': fun.nloc,
                     'lines': fun.length,
                     'name': fun.name,
                     'args': fun.parameter_count,
                     'start': fun.start_line,
                     'end': fun.end_line
                })

        return overall, funs