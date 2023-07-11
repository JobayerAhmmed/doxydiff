import os
import filecmp



def diff_dirs(initial_path, new_path, accurate_mode):
    """
    Given two directories, compare them and find same, changed,
    added, deleted, renamed files.
    Then compare each pair of files.

    :type initial_path: object
    :param initial_path: initial dir to diff against
    :type new_path: object
    :param new_path: new dir to compare to initial dir
    :type accurate_mode: boolean
    :param accurate_mode: use accurate mode or not
    :returns: string containing diffed html from initial_path and new_path
    """
    pass


def compare_dir(dir_a, dir_b):
    filecmp.clear_cache()
    dcmp = filecmp.dircmp(dir_a, dir_b)
    no_change, changed, added, deleted, renamed = [], [], [], [], []
    diff_files(dcmp, no_change, changed, added, deleted, renamed)


def diff_files(dcmp, no_change, changed, added, deleted, renamed):
    for name in dcmp.same_files:
        no_change.append((os.path.join(dcmp.left, name), os.path.join(dcmp.right, name)))
    for name in dcmp.diff_files:
        changed.append((os.path.join(dcmp.left, name), os.path.join(dcmp.right, name)))
    for name in dcmp.left_only:
        filepath = os.path.join(dcmp.left, name)
        if os.path.isdir(filepath):
            for root, _, files in os.walk(filepath):
                for filename in files:
                    deleted.append(os.path.join(root, filename))
        else:
            deleted.append(filepath)
    for name in dcmp.right_only:
        filepath = os.path.join(dcmp.right, name)
        if os.path.isdir(filepath):
            for root, _, files in os.walk(filepath):
                for filename in files:
                    added.append(os.path.join(root, filename))
        else:
            added.append(filepath)
    for sub_dcmp in dcmp.subdirs.values():
        diff_files(sub_dcmp, no_change, changed, added, deleted, renamed)

