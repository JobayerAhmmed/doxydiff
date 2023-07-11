import sys

if (sys.version_info < (3, 0)):
    from HTMLParser import HTMLParser
else:
    from html.parser import HTMLParser

import os
import filecmp
import logging
import shutil
from pathlib import Path
from lxml import etree
from htmldiff.lib import diff_files, gen_side_by_side



LOG = logging.getLogger(__name__)


def create_dir_diff(initial_path, new_path, accurate_mode, output_dir):
    """
    Given two directories, compare them and find same, changed,
    added, deleted, renamed files.
    Then compare each pair of files and write the compared files
    to the output directory.

    :type initial_path: object
    :param initial_path: initial dir to diff against
    :type new_path: object
    :param new_path: new dir to compare to initial dir
    :type accurate_mode: boolean
    :param accurate_mode: use accurate mode or not
    :type output_dir: object
    :param output_dir: output directory to store the diff files
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    no_change, changed, added, deleted, renamed = compare_dir(initial_path, new_path)

    for index, item in enumerate(no_change):
        relative_path = item[1].lstrip(new_path)
        output_file = os.path.join(output_dir, relative_path)
        Path(os.path.dirname(output_file)).mkdir(parents=True, exist_ok=True)
        print('[{0}/{1}] identical [skipped]: {2}'.format(index+1, len(no_change), output_file))
        shutil.copy2(item[1], output_file)

    # If CREATE_SUBDIRS=YES is set in Doxyfile,
    # then doxygen will create output in subdirs.
    # Maximum level: 8
    # The first level always has a fixed numer of 16 directories.
    # run_file_diff() for those files that are in those subdirs.
    paths_len = len(Path(new_path).parents)
    paths_len += 3 # self, 'html', 'd0'
    for index, item in enumerate(changed):
        relative_path = item[1].lstrip(new_path)
        output_file = os.path.join(output_dir, relative_path)
        Path(os.path.dirname(output_file)).mkdir(parents=True, exist_ok=True)
        if item[1].endswith(('c.html', 'h.html')) and len(Path(item[1]).parents) >= paths_len:
            print('[{0}/{1}] modified [diffing]: {2}'.format(index+1, len(changed), output_file))
            run_file_diff(item[0], item[1], accurate_mode, output_file)
        else:
            print('[{0}/{1}] modified [skipped]: {2}'.format(index+1, len(changed), output_file))
            shutil.copy2(item[1], output_file)

    color_insert = '#AFA;'
    for index, item in enumerate(added):
        relative_path = item.lstrip(new_path)
        output_file = os.path.join(output_dir, relative_path)
        Path(os.path.dirname(output_file)).mkdir(parents=True, exist_ok=True)
        print('[{0}/{1}] added: {2}'.format(index+1, len(added), output_file))
        if item.endswith('.html'):
            update_file(item, output_file, color_insert)
        else:
            shutil.copy2(item, output_file)

    color_delete = '#F88;'
    for index, item in enumerate(deleted):
        relative_path = item.lstrip(initial_path)
        output_file = os.path.join(output_dir, relative_path)
        Path(os.path.dirname(output_file)).mkdir(parents=True, exist_ok=True)
        print('[{0}/{1}] deleted: {2}'.format(index+1, len(deleted), output_file))
        if item.endswith('.html'):
            update_file(item, output_file, color_delete)
        else:
            shutil.copy2(item, output_file)

    LOG.info('Wrote diff to {0}'.format(output_file))
    sys.exit(0)


def compare_dir(dir_a, dir_b):
    filecmp.clear_cache()
    dcmp = filecmp.dircmp(dir_a, dir_b)
    no_change, changed, added, deleted, renamed = [], [], [], [], []
    filter_files(dcmp, no_change, changed, added, deleted, renamed)
    return no_change, changed, added, deleted, renamed


def filter_files(dcmp, no_change, changed, added, deleted, renamed):
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
        filter_files(sub_dcmp, no_change, changed, added, deleted, renamed)


def run_file_diff(input_file1, input_file2, accurate_mode, output_file):
    try:
        diffed_html = diff_files(input_file1, input_file2, accurate_mode)
        diffed_html = gen_side_by_side(diffed_html)
    except Exception:
        LOG.exception('Diff process exited with an error for files: ' + input_file1, ' and ' + input_file2)
        sys.exit(1)

    try:
        with open(output_file, 'w') as f:
            f.seek(0)
            f.truncate()
            f.write(diffed_html)
    except Exception:
        LOG.exception('Unable to write diff to {0}'.format(output_file))
        sys.exit(1)


def update_file(filepath, output_file, color):
    parser = etree.HTMLParser()
    tree = etree.parse(filepath, parser)
    contents = tree.xpath("//div[contains(concat(' ', normalize-space(@class), ' '), 'contents')]")
    for el in contents:
        el.set('style', 'background-color: ' + color)
    header = tree.xpath("//div[contains(concat(' ', normalize-space(@class), ' '), 'header')]")
    for el in header:
        el.set('style', 'background-color: ' + color)
    tree.write(output_file, method='html')
    
