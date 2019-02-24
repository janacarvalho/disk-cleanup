"""This module is used to delete unused file scene versions."""

import sys
import os
import re
import time
from operator import itemgetter


LOG_PATH = 'C:\\temp\\ASSETS'
EMPTY_FILES_LOG = 'empty_files_log'
EMPTY_FOLDERS_LOG = 'empty_folders_log'
ORPHAN_THUMB_LOG = 'orphan_thumbnails_log'
EXTRA_VERSIONS_LOG = 'extra_versions_log'


class DiskCleanup:

    def __init__(self, path):
        self.path = path
        self.mb_folder_list = self.get_mb_folder_list()

    def get_mb_folder_list(self):
        pattern = re.compile(r'(\S+)(dir_)(\S+)-(\d+)(\.mb)$')
        mb_folder_list = []
        for root, _, _ in os.walk(self.path):
            if re.match(pattern, root) is not None:
                mb_folder_list.append(root)
        return mb_folder_list

    def delete_empty_files(self):
        zip_pattern = re.compile(r'(\S+)(\.mb)_(\d+\.\d+)(\.zip)$')
        timestamp = time.strftime('%Y%m%d_%H%M%S', time.gmtime(time.time()))
        log_full_path = os.path.join(LOG_PATH, EMPTY_FILES_LOG + timestamp + '.txt')
        log_file = open(log_full_path, 'w')
        for folder_path in self.mb_folder_list:
            dir_content = os.listdir(folder_path)
            for f in dir_content:
                file_fullname = os.path.join(folder_path, f)
                if os.path.isfile(file_fullname) and re.match(zip_pattern, file_fullname) is not None \
                        and os.path.getsize(file_fullname) == 0:
                    file_data = os.stat(file_fullname)
                    try:
                        os.remove(file_fullname)
                        log_file.write("<Deleted file>\t modified: {}\t size: {}KB\t file: {}\n"
                                       .format(time.strftime('%Y/%m/%d %H:%M:%S', time.gmtime(file_data.st_mtime)),
                                               file_data.st_size, file_fullname))
                        sys.stdout.write("<Deleted file>\t modified: {}\t size: {}KB\t file: {}\n"
                                         .format(time.strftime('%Y/%m/%d %H:%M:%S', time.gmtime(file_data.st_mtime)),
                                                 file_data.st_size, file_fullname))
                    except Exception as error:
                        print error
                        log_file.write("<Unable to delete file>\t modified: {}\t size: {}KB\t file: {}\n"
                                       .format(time.strftime('%Y/%m/%d %H:%M:%S', time.gmtime(file_data.st_mtime)),
                                               file_data.st_size, file_fullname))
                        sys.stdout.write("<Unable to delete file>\t modified: {}\t size: {}KB\t file: {}\n"
                                         .format(time.strftime('%Y/%m/%d %H:%M:%S', time.gmtime(file_data.st_mtime)),
                                                 file_data.st_size, file_fullname))
                        continue
                    sys.stdout.flush()
        log_file.close()

    def delete_empty_folders(self):
        timestamp = time.strftime('%Y%m%d_%H%M%S', time.gmtime(time.time()))
        log_full_path = os.path.join(LOG_PATH, EMPTY_FOLDERS_LOG + timestamp + '.txt')
        log_file = open(log_full_path, 'w')
        directory_list = []
        for dir_name, _, _ in os.walk(self.path):
            directory_list.append(dir_name)
        directory_list.reverse()
        for directory in directory_list:
            if not os.listdir(directory):
                try:
                    os.rmdir(directory)
                    log_file.write("<Deleted folder> \t{}\n".format(directory))
                    sys.stdout.write("<Deleted folder> \t{}\n".format(directory))
                except Exception as error:
                    print error
                    log_file.write("<Unable to delete folder> \t{}\n".format(directory))
                    sys.stdout.write("<Unable to delete folder> \t{}\n".format(directory))
                    continue
                sys.stdout.flush()
        log_file.close()

    def delete_extra_versions(self, ret_versions=3, mod_days=100):
        timestamp = time.strftime('%Y%m%d_%H%M%S', time.gmtime(time.time()))
        log_full_path = os.path.join(LOG_PATH, EXTRA_VERSIONS_LOG + timestamp + '.txt')
        log_file = open(log_full_path, 'w')

        current_time = time.time()
        for folder in self.mb_folder_list:
            file_dict = group_versions(folder)
            real_versions = []
            for ver in file_dict:
                if 'zip_file' in file_dict[ver]:
                    real_versions.append(ver)
            real_versions = sort_versions(real_versions)

            is_old = False
            for version in real_versions:
                modified_date = os.stat(file_dict[version]['zip_file']).st_mtime
                if ((current_time - modified_date) / 3600 / 24) < mod_days:
                    is_old = False
                    break
                else:
                    is_old = True
            if is_old:  # use ret_versions to keep the number of versions
                versions_to_delete = real_versions[ret_versions:]
                for version in versions_to_delete:
                    file_name = file_dict[version]['zip_file']
                    try:
                        # os.remove(file_name)
                        log_file.write("<Deleted old version> \t{}\n".format(file_name))
                        sys.stdout.write("<Deleted old version> \t{}\n".format(file_name))
                    except Exception as error:
                        print error
                        log_file.write("<Unable to delete old version> \t{}\n".format(file_name))
                        sys.stdout.write("<Unable to delete old version> \t{}\n".format(file_name))
                        continue
                    sys.stdout.flush()
            else:  # use mod_days to delete versions older than that
                versions_to_delete = real_versions[:]

        log_file.close()

    def delete_orphan_thumbnails(self):
        timestamp = time.strftime('%Y%m%d_%H%M%S', time.gmtime(time.time()))
        log_full_path = os.path.join(LOG_PATH, ORPHAN_THUMB_LOG + timestamp + '.txt')
        log_file = open(log_full_path, 'w')
        for folder in self.mb_folder_list:
            versions_dict = group_versions(folder)
            for ver in versions_dict:
                if 'zip_file' not in versions_dict[ver]:
                    file_name = versions_dict[ver]['thumbnail']
                    try:
                        os.remove(versions_dict[ver]['thumbnail'])
                        log_file.write("<Deleted orphan thumbnail> \t{}\n".format(file_name))
                        sys.stdout.write("<Deleted orphan thumbnail> \t{}\n".format(file_name))
                    except Exception as error:
                        print error
                        log_file.write("<Unable to delete thumbnail> \t{}\n".format(file_name))
                        sys.stdout.write("<Unable to delete thumbnail> \t{}\n".format(file_name))
                        continue
                    sys.stdout.flush()
        log_file.close()

    def delete_old_versions(ret_days, path):
        current_time = time.time()
        ret_days_sec = ret_days * 3600 * 24
        file_list = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
        for zip_file in file_list:
            file_data = os.stat(os.path.join(path, zip_file))
            if (current_time - file_data.st_mtime) > ret_days_sec:
                size = file_data.st_size/1024 if file_data.st_size/1024 > 1 else 1
                print "{} \t {} \t {} KB".format(os.path.join(path, zip_file), time.ctime(file_data.st_atime), size)
                os.remove(os.path.join(path, zip_file))


def group_versions(path):
    pattern = r'(\w\:)(\S+\\)(\S+\.mb)_(\d+\.\d+)(\.\w{3})'
    # group 1: drive
    # group 2: directory
    # group 3: scene
    # group 4: scene version
    # group 5: file extension
    file_list = []
    folder_dict = {}
    dir_content = os.listdir(path)
    for f in dir_content:
        file_fullname = os.path.join(path, f)
        if os.path.isfile(file_fullname) and re.match(pattern, file_fullname) is not None:
            file_list.append(file_fullname)
    for filename in file_list:
        match_group = re.search(pattern, filename)
        version = match_group.group(4)
        extension = match_group.group(5)
        if version in folder_dict:
            if extension.lower() == '.jpg':
                folder_dict[version].update({'thumbnail': filename})
            if extension.lower() == '.zip':
                folder_dict[version].update({'zip_file': filename})
        else:
            if extension.lower() == '.jpg':
                folder_dict.update({version: {'thumbnail': filename}})
            if extension.lower() == '.zip':
                folder_dict.update({version: {'zip_file': filename}})
    return folder_dict


def sort_versions(version_list):
    str_to_list = [item.split('.') for item in version_list]
    str_list_to_int = [[int(item) for item in sub_list] for sub_list in str_to_list]
    sorted_list = sorted(str_list_to_int, key=itemgetter(0,1))
    int_to_str = [[str(item) for item in sub_list] for sub_list in sorted_list]
    list_to_str = ['.'.join(item) for item in int_to_str]
    list_to_str.reverse()
    return list_to_str


def main(argv):
    assets = DiskCleanup(argv)
    assets.delete_empty_files()
    assets.delete_extra_versions(5)
    assets.delete_orphan_thumbnails()
    assets.delete_empty_folders()


if __name__ == '__main__':
    # main(sys.argv[1])
    main("C:\\temp\\ASSETS")
