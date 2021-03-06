"""
Library with file tools.
"""

import os


# IMPORTANT COMMENT: In order to make @property and setters work, you need to define the class using OBJECT between
# parenthesis or it won't work
class FilePath(object):
    """
    Class to handle file information: FilePath name, root, extension, etc...
    """
    def __init__(self, *u_path):
        self.u_path = os.path.join(*u_path)
        self.u_root = os.path.dirname(self.u_path)
        self.u_file = os.path.basename(self.u_path)
        self.u_name = self.u_file.rpartition('.')[0]
        self._u_ext = self.u_file.rpartition('.')[2]

    def __str__(self):
        u_output = u'<FilePath>\n'
        u_output += u'  .u_path:   %s\n' % self.u_path
        u_output += u'  .u_root:   %s\n' % self.u_root
        u_output += u'  .u_file:   %s\n' % self.u_file
        u_output += u'  .u_name:   %s\n' % self.u_name
        u_output += u'  .u_format: %s\n' % self.u_ext

        return u_output.encode('utf8')

    # I don't totally agree that properties + setters/getters are that better. In one one, it's true that your class
    # code will look cleaner since you won't be creating as many set_x, set_y functions. But, on the other hand, when
    # you modify your instances from outside, IT'S NOT CLEAR AT ALL THAT YOU ARE ACTUALLY CALLING A METHOD INSTEAD OF
    # SIMPLY MODIFYING ONE SINGLE PROPERTY.
    #
    # But apparently it's the way it should be. Read, for example:
    #
    #     http://2ndscale.com/rtomayko/2005/getters-setters-fuxors

    def get_u_ext(self):
        return self._u_ext

    def set_u_ext(self, u_new_ext):
        self._u_ext = u_new_ext
        self.u_file = u'%s.%s' % (self.u_name, u_new_ext)
        self.u_path = os.path.join(self.u_root, self.u_file)

    u_ext = property(get_u_ext, set_u_ext)

    def is_child_of(self, po_parent_path):
        """
        Method to check if a the PilePath object is inside another path.
        :type po_path: FilePath
        :return:
        """

    def absfile(self):
        """
        Method that returns a new FilePath object with the path normalized.
        :return: a FilePath object.
        """
        u_abs_path = os.path.abspath(self.u_path.encode('utf8')).decode('utf8')
        o_abs_file = FilePath(u_abs_path)
        return o_abs_file

    def content(self, pb_recursive=False, pu_mode='all'):
        """
        Method that returns a list with the contents of the file object. If the file object is a file, the content will
        be always empty since a file doesn't contain other files or directories.

        :param pb_recursive: If True, the content search will be recursive.

        :return: A list of FilePath objects
        """

        lo_raw_file_objects = []

        if self.is_dir():
            if not pb_recursive:
                for u_element in os.listdir(self.u_path):
                    u_full_path = os.path.join(self.u_path, u_element)
                    o_file_object = FilePath(u_full_path)
                    lo_raw_file_objects.append(o_file_object)

            else:
                for u_root, lu_dirs, lu_files in os.walk(self.u_path):
                    lu_elements = lu_dirs + lu_files
                    for u_element in lu_elements:
                        u_full_path = os.path.join(u_root, u_element)
                        o_fp = FilePath(u_full_path)
                        lo_raw_file_objects.append(o_fp)

        lo_clean_file_objects = []
        for o_element_fp in lo_raw_file_objects:
            b_valid = False

            if pu_mode == 'all':
                b_valid = True
            if pu_mode == 'dirs' and o_element_fp.is_dir():
                b_valid = True
            elif pu_mode == 'files' and o_element_fp.is_file():
                b_valid = True

            if b_valid:
                lo_clean_file_objects.append(o_element_fp)

        # os.listdir doesn't return elements sorted in any way, and maybe os.walk neither so I have to do it manually.
        lo_clean_file_objects.sort(key=lambda x: x.u_path, reverse=False)

        return lo_clean_file_objects

    def exists(self):
        """
        Method that checks if the path exists or not.
        :return: True/False
        """
        if os.path.exists(self.u_path):
            b_exists = True
        else:
            b_exists = False

        return b_exists

    def root_exists(self):
        """
        Method to check if the root path exists or not.
        :return: True/False
        """
        if os.path.isdir(self.u_root):
            b_exists = True
        else:
            b_exists = False

        return b_exists

    def root_replace(self, pu_prev, pu_new):
        u_new_path = self.u_path.replace(pu_prev, pu_new, 1)
        #print '---', self.u_path
        #print '+++', u_new_path
        return FilePath(u_new_path)

    def root_prepend(self, *pu_path):
        """
        Method to add extra elements at the beginning of the root. i.e. cc/dd.jpg -> aa/bb/cc/dd.jpg
        :param pu_path: Elements to prepend. i.e. "aa", "bb"
        :return: Nothing
        """
        print '0: %s' % pu_path
        print '1: %s' % self.u_root
        print os.path.join(pu_path, self.u_root)
        import sys
        sys.exit()

    def has_exts(self, *plu_exts):
        """
        Method to check if the FilePath object has certain extension no matter the casing.

        :param u_ext: Extension to test. i.e. 'jpg'

        :return: True/False, if the file extension matches or not (casi insensitive, jpg and JPG will output the same
                 result).
        """

        b_has_ext = False

        for u_ext in plu_exts:
            if self.u_ext.lower() == u_ext.lower():
                b_has_ext = True
                break

        return b_has_ext

    def is_dir(self):
        """
        Method to check if the file object is a directory.

        :return: True/False
        """

        if self.exists() and os.path.isdir(self.u_path):
            b_is_dir = True

        else:
            b_is_dir = False

        return b_is_dir

    def is_file(self):
        """
        Method to check if the file object is a file.

        :return: True/False
        """

        if self.exists() and os.path.isfile(self.u_path):
            b_is_file = True

        else:
            b_is_file = False

        return b_is_file

    def get_file_in_subdirs(self, pu_file, *subdirs):
        """
        Method to get the first appearance of a file in certain list of subdirs.

        For example, if we have:

            folder_1
                aaa.png
            folder_2
                aaa.png

        And we call .get_file_in_subdirs('aaa.png', 'folder_1', 'folder_2'). The fp object of folder_1/aaa.png will be
        returned.

        :type pu_file: unicode Name of the file to search for.

        :type subdirs: unicode Name of the directories to search for by the order we want to search.

        :return: The first matched FilePath object if the file exists, None in other case.
        """
        if self.is_file():
            raise ValueError
        else:
            o_matched_fp = None
            for u_subdir in subdirs:
                o_candidate_fp = FilePath(self.u_path, u_subdir, pu_file)
                print o_candidate_fp
                if o_candidate_fp.is_file():
                    o_matched_fp = o_candidate_fp
                    break

            return o_matched_fp


def get_cwd():
    """
    Function to get the current working directory.

    :return: A FilePath object.
    """
    u_cwd = os.getcwd().decode('utf8')
    o_cwd = FilePath(u_cwd)
    return o_cwd


def read_nlines(po_file, pi_lines):
    """
    Function to read n lines from a file
    :param po_file:
    :param pi_lines:
    :return:
    """
    i_line = 0
    lu_lines = []

    try:
        for u_line in po_file:
            i_line += 1
            lu_lines.append(u_line.rstrip(u'\n'))
            if i_line == pi_lines:
                break

    except IOError:
        pass

    return lu_lines