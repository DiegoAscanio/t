#!/usr/bin/env python

"""t is for people that want do things, not organize their tasks."""

from __future__ import with_statement, print_function

import os, re, sys, hashlib
from optparse import OptionParser, OptionGroup
import string
import numpy as np

class InvalidTaskfile(Exception):
    """Raised when the path to a task file already exists as a directory."""
    pass

class AmbiguousPrefix(Exception):
    """Raised when trying to use a prefix that could identify multiple tasks."""
    def __init__(self, prefix):
        super(AmbiguousPrefix, self).__init__()
        self.prefix = prefix

class UnknownPrefix(Exception):
    """Raised when trying to use a prefix that does not match any tasks."""
    def __init__(self, prefix):
        super(UnknownPrefix, self).__init__()
        self.prefix = prefix

class BadFile(Exception):
    """Raised when something else goes wrong trying to work with the task file."""
    def __init__(self, path, problem):
        super(BadFile, self).__init__()
        self.path = path
        self.problem = problem

def _hash(text):
    """Return a hash of the given text for use to retrieve tasks by ID.

    Currently SHA1 hashing is used.  It should be plenty for our purposes.

    """
    return hashlib.sha1(text.encode('utf-8')).hexdigest()



# Define the base 62 alphabet: 0-9, A-Z, a-z (a total of 62 characters)
ALPHABET_BASE62 = string.digits + string.ascii_uppercase + string.ascii_lowercase
BASE = len(ALPHABET_BASE62) # BASE = 62

# --- Auxiliary Mathematical Functions ---

def _mod_inverse(a, m):
    """Finds the modular multiplicative inverse of 'a' modulo 'm'."""
    # The inverse only exists if gcd(a, m) == 1.
    g, x, y = _extended_gcd(a, m)
    if g != 1:
        return None
    return (x % m + m) % m

def _extended_gcd(a, b):
    """Extended Euclidean Algorithm to find gcd(a, b) and coefficients."""
    if a == 0:
        return b, 0, 1
    gcd, x1, y1 = _extended_gcd(b % a, a)
    x = y1 - (b // a) * x1
    y = x1
    return gcd, x, y

def _char_to_num(char):
    """Converts a character to its numerical value in base 62."""
    return ALPHABET_BASE62.index(char)

def _num_to_char(num):
    """Converts a numerical value to its character in base 62."""
    return ALPHABET_BASE62[num]

# --- Main Cipher and Decipher Functions (Using NumPy) ---

def _encrypt_base_62(plaintext, key_matrix = [
    [1, 5, 10,  2],
    [0, 1, 3,   7],
    [0, 0, 1,   4],
    [0, 0, 0, 991]
    ]):
    """Encrypts a plaintext message in base 62 using an N x N key with NumPy."""
    # Convert the Python list to a NumPy array and check if it's square
    key_matrix_np = np.array(key_matrix, dtype=int)
    N = key_matrix_np.shape[0]
    if key_matrix_np.shape[0] != key_matrix_np.shape[1]:
        raise ValueError("The key must be a square matrix (N x N).")
        
    plaintext = "".join(c for c in plaintext if c in ALPHABET_BASE62)
    
    # Auto-padding to ensure the length is a multiple of N
    if len(plaintext) % N != 0:
        plaintext += '0' * (N - (len(plaintext) % N))

    ciphertext = ""
    for i in range(0, len(plaintext), N):
        block = plaintext[i:i+N]
        # Convert block to a numerical vector (NumPy column array)
        p_vector = np.array([_char_to_num(c) for c in block], dtype=int).reshape(N, 1)
        
        # Matrix multiplication: Key * p_vector mod BASE
        # numpy.dot performs matrix multiplication
        c_vector = np.dot(key_matrix_np, p_vector) % BASE
            
        # Convert the ciphered vector back to characters
        ciphertext += "".join(_num_to_char(c[0]) for c in c_vector)
        
    return ciphertext

def _decrypt_base_62(ciphertext, key_matrix = [
    [1, 5, 10,  2],
    [0, 1, 3,   7],
    [0, 0, 1,   4],
    [0, 0, 0, 991]
    ]):
    """Decrypts a ciphertext message in base 62 using the N x N key with NumPy."""
    key_matrix_np = np.array(key_matrix, dtype=int)
    N = key_matrix_np.shape[0]

    if len(ciphertext) % N != 0:
        raise ValueError("The length of the ciphertext must be a multiple of N.")

    # --- Modular Matrix Inverse Calculation using NumPy and custom logic ---

    # 1. Calculate the determinant of the original matrix
    # Use numpy.linalg.det, rounded to ensure it is an integer
    det = round(np.linalg.det(key_matrix_np))
    det_mod62 = det % BASE
    
    # 2. Find the modular inverse of the determinant
    det_inv = _mod_inverse(det_mod62, BASE)

    if det_inv is None:
        raise ValueError(f"Determinant ({det_mod62}) is not invertible mod {BASE}. Choose a different key.")

    # 3. Calculate the real inverse matrix using NumPy and convert to modular
    # numpy.linalg.inv() calculates the inverse using floats
    inv_matrix_float = np.linalg.inv(key_matrix_np)
    # The adjugate matrix is det * inv_matrix (rounded to nearest int)
    adjugate_matrix = (det * inv_matrix_float).round().astype(int)

    # 4. Multiply the adjugate by the modular inverse of the determinant and apply mod BASE
    inv_key_matrix_mod = (adjugate_matrix * det_inv) % BASE

    # --- Decryption Process ---
    plaintext = ""
    for i in range(0, len(ciphertext), N):
        block = ciphertext[i:i+N]
        # Convert block to a numerical vector (NumPy column array)
        c_vector = np.array([_char_to_num(c) for c in block], dtype=int).reshape(N, 1)
        
        # Matrix multiplication: Inverse_Key_Matrix * c_vector mod BASE
        p_vector = np.dot(inv_key_matrix_mod, c_vector) % BASE
            
        # Convert the deciphered vector back to characters
        plaintext += "".join(_num_to_char(p[0]) for p in p_vector)
        
    return plaintext

_encrypt = _encrypt_base_62
_decrypt = _decrypt_base_62

def _id():
    """Return a new unique ciphered base62 ID sortable for a task."""
    global _id_counter
    _id_counter += 1
    plaintext_id = f'{_id_counter:06d}'
    ciphered_id = _encrypt(plaintext_id)
    return ciphered_id

def _parse_text_and_metadata_from_taskline(line: str):
    text, sep, content = line.partition('|')
    return (text.strip(), content.strip()) if sep else (line.strip(), None)

def _build_task(text, metadata = None):
    task = { 'text': text }
    if metadata:
        for piece in metadata.strip().split(','):
            label, data = piece.split(':')
            task[label.strip()] = data.strip()
    return task

def _taskline_from_task(task):
    """Parse a task into a taskline suitable for writing."""
    meta = [m for m in task.items() if m[0] != 'text']
    meta_str = ', '.join('%s:%s' % m for m in meta)
    return '%s | %s\n' % (task['text'], meta_str)

def _tasklines_from_tasks(tasks):
    """Parse a list of tasks into tasklines suitable for writing."""

    tasklines = [
            _taskline_from_task(task) for task in tasks
            ]
    return tasklines

def _prefixes(ids):
    """Return a mapping of ids to prefixes in O(n) time.

    Each prefix will be the shortest possible substring of the ID that
    can uniquely identify it among the given group of IDs.

    If an ID of one task is entirely a substring of another task's ID, the
    entire ID will be the prefix.
    """
    ps = {}
    for id in ids:
        id_len = len(id)
        for i in range(1, id_len+1):
            # identifies an empty prefix slot, or a singular collision
            prefix = id[:i]
            if (not prefix in ps) or (ps[prefix] and prefix != ps[prefix]):
                break
        if prefix in ps:
            # if there is a collision
            other_id = ps[prefix]
            for j in range(i, id_len+1):
                if other_id[:j] == id[:j]:
                    ps[id[:j]] = ''
                else:
                    ps[other_id[:j]] = other_id
                    ps[id[:j]] = id
                    break
            else:
                ps[other_id[:id_len+1]] = other_id
                ps[id] = id
        else:
            # no collision, can safely add
            ps[prefix] = id
    ps = dict(zip(ps.values(), ps.keys()))
    if '' in ps:
        del ps['']
    return ps

def _summary_line(taskline):
    """Return if a line is a summary line"""
    _, sep, _ = taskline.partition('|')
    return sep == ''

def _ensure_tasklines_consistency(tls, default_start = 0):
    """
    Ensure that after a summary line is found, all subsequent lines will
    be transformed into summary lines, so every task has a unique and
    sortable ID.
    """
    summary_lines = list(map(_summary_line, tls))
    summary_idx = summary_lines.index(True) if True in summary_lines else -1
    if summary_idx != -1:
        _ensure_id_counter_consistency_for_summary_tasks(summary_idx, default_start = default_start)
        for i in range(summary_idx, len(tls)):
            if not _summary_line(tls[i]):
                text, _ = _parse_text_and_metadata_from_taskline(tls[i])
                tls[i] = text
    return tls

def _ensure_id_counter_consistency_for_summary_tasks(summary_idx, default_start = 0):
    """
    Ensure that the global ID counter is set to the value of the last
    non-summary task's ID + 1, so that newly created tasks will
    have unique IDs. That is the index of the first summary line +
    default_start.
    """
    global _id_counter
    _id_counter = default_start + summary_idx - 1

def _ensure_id_counter_consistency_for_current_task(task):
    '''
    Ensure that the global ID counter is set to the value of the
    current task's ID, so that newly created tasks will have its
    ID + 1.
    '''
    global _id_counter
    if task is not None:
        task_id_decrypted = int(_decrypt(task['id']))
        _id_counter = task_id_decrypted

def _task_from_taskline(line, tasks_hashes_id_map):
    """Parse a taskline (from a task file) and return a task.

    A taskline should be in the format:

        summary text ... | meta1:meta1_value,meta2:meta2_value,...

    The task returned will be a dictionary such as:

        { 'id': <hash id>,
          'text': <summary text>,
           ... other metadata ... }

    """
    if line.strip().startswith('#'): # Skip comments
        return None
    text, metadata = _parse_text_and_metadata_from_taskline(line)
    task = _build_task(text, metadata)
    if 'id' not in task:
        task['id'] = tasks_hashes_id_map.get(_hash(text)) or _id()
        tasks_hashes_id_map[_hash(text)] = task['id']
    return task

def _handle_tasks(tls, tasks_hashes_id_map):
    """
    Given a list of properly consistent tasklines, return the corresponding tasks.
    """
    global _id_counter
    tasks = []
    for line in tls:
        task = _task_from_taskline(line, tasks_hashes_id_map)
        tasks += [task] if task not in tasks else []
        # update global ID counter to ensure consistency
        _ensure_id_counter_consistency_for_current_task(task)
    return tasks


class TaskDict(object):
    """A set of tasks, both finished and unfinished, for a given list.

    The list's files are read from disk when the TaskDict is initialized. They
    can be written back out to disk with the write() function.

    """
    def __init__(self, taskdir='.', name='tasks', default_start=0):
        """Initialize by reading the task files, if they exist."""
        self.tasks = {}
        self.tasks_hashes_id_map = {}
        self.done = {}
        self.name = name
        self.taskdir = taskdir
        filemap = (('tasks', self.name), ('done', '.%s.done' % self.name))
        for kind, filename in filemap:
            path = os.path.join(os.path.expanduser(self.taskdir), filename)
            if os.path.isdir(path):
                raise InvalidTaskfile
            if os.path.exists(path):
                try:
                    with open(path, 'r') as tfile:
                        tls = [tl.strip() for tl in tfile if tl]
                        tls = _ensure_tasklines_consistency(tls, default_start=default_start)
                        tasks = _handle_tasks(
                            tls,
                            self.tasks_hashes_id_map
                        )
                        for task in tasks:
                            if task is not None:
                                # 1. Add task to self.tasks dict if it
                                # is unfinished (kind == 'tasks')
                                getattr(self, kind)[task['id']] = task
                                # 2. Map hash of text to id to avoid task duplication
                                self.tasks_hashes_id_map[_hash(task['text'])] = task['id']
                except IOError as e:
                    raise BadFile(path, e.strerror)
        # then we call self.write() to flush any changes back out
        # to disk when needed
        self.write()

    def __getitem__(self, prefix):
        """Return the unfinished task with the given prefix.

        If more than one task matches the prefix an AmbiguousPrefix exception
        will be raised, unless the prefix is the entire ID of one task.

        If no tasks match the prefix an UnknownPrefix exception will be raised.

        """
        matched = [tid for tid in self.tasks.keys() if tid.startswith(prefix)]
        if len(matched) == 1:
            return self.tasks[matched[0]]
        elif len(matched) == 0:
            raise UnknownPrefix(prefix)
        elif prefix in matched:
            return self.tasks[prefix]
        else:
            raise AmbiguousPrefix(prefix)

    def add_task(self, text, verbose, quiet):
        """Add a new, unfinished task with the given summary text."""
        task_id = self.tasks_hashes_id_map.get(_hash(text)) or _id()
        self.tasks[task_id] = {'id': task_id, 'text': text}

        if not quiet:
            if verbose:
                print(task_id)
            else:
                prefixes = _prefixes(self.tasks)
                print(prefixes[task_id])

    def edit_task(self, prefix, text):
        """Edit the task with the given prefix.

        If more than one task matches the prefix an AmbiguousPrefix exception
        will be raised, unless the prefix is the entire ID of one task.

        If no tasks match the prefix an UnknownPrefix exception will be raised.

        """
        task = self[prefix]
        if text.startswith('s/') or text.startswith('/'):
            text = re.sub('^s?/', '', text).rstrip('/')
            find, _, repl = text.partition('/')
            text = re.sub(find, repl, task['text'])

        task['text'] = text
        # we should keep our ID, so we won't change it

    def finish_task(self, prefix):
        """Mark the task with the given prefix as finished.

        If more than one task matches the prefix an AmbiguousPrefix exception
        will be raised, if no tasks match it an UnknownPrefix exception will
        be raised.

        """
        task = self.tasks.pop(self[prefix]['id'])
        self.done[task['id']] = task

    def remove_task(self, prefix):
        """Remove the task from tasks list.

        If more than one task matches the prefix an AmbiguousPrefix exception
        will be raised, if no tasks match it an UnknownPrefix exception will
        be raised.

        """
        self.tasks.pop(self[prefix]['id'])


    def print_list(self, kind='tasks', verbose=False, quiet=False, grep=''):
        """Print out a nicely formatted list of unfinished tasks."""
        tasks = dict(getattr(self, kind).items())
        label = 'prefix' if not verbose else 'id'

        if not verbose:
            for task_id, prefix in _prefixes(tasks).items():
                tasks[task_id]['prefix'] = prefix

        plen = max(map(lambda t: len(t[label]), tasks.values())) if tasks else 0
        for _, task in sorted(
            tasks.items(),
            key = lambda x: int(_decrypt(x[1]['id']))
        ):
            if grep.lower() in task['text'].lower():
                p = '%s - ' % task[label].ljust(plen) if not quiet else ''
                print(p + task['text'])

    def write(self, delete_if_empty=False):
        """Flush the finished and unfinished tasks to the files on disk."""
        filemap = (('tasks', self.name), ('done', '.%s.done' % self.name))
        for kind, filename in filemap:
            path = os.path.join(os.path.expanduser(self.taskdir), filename)
            if os.path.isdir(path):
                raise InvalidTaskfile
            tasks = sorted(
                getattr(self, kind).values(), key = lambda x: int(_decrypt(x['id']))
            )
            if tasks or not delete_if_empty:
                try:
                    with open(path, 'w') as tfile:
                        for taskline in _tasklines_from_tasks(tasks):
                            tfile.write(taskline)
                except IOError as e:
                    raise BadFile(path, e.strerror)

            elif not tasks and os.path.isfile(path):
                os.remove(path)


def _die(message):
    sys.stderr.write('error: %s\n' % message)
    sys.exit(1)

def _build_parser():
    """Return a parser for the command-line interface."""
    usage = "Usage: %prog [-t DIR] [-l LIST] [options] [TEXT]"
    parser = OptionParser(usage=usage)

    actions = OptionGroup(parser, "Actions",
                          "If no actions are specified the TEXT will be added as a new task.")
    actions.add_option("-e", "--edit", dest="edit", default="",
                       help="edit TASK to contain TEXT", metavar="TASK")
    actions.add_option("-f", "--finish", dest="finish",
                       help="mark TASK as finished", metavar="TASK")
    actions.add_option("-r", "--remove", dest="remove",
                       help="Remove TASK from list", metavar="TASK")
    parser.add_option_group(actions)

    config = OptionGroup(parser, "Configuration Options")
    config.add_option("-l", "--list", dest="name", default="tasks",
                      help="work on LIST", metavar="LIST")
    config.add_option("-t", "--task-dir", dest="taskdir", default="",
                      help="work on the lists in DIR", metavar="DIR")
    config.add_option("-d", "--delete-if-empty",
                      action="store_true", dest="delete", default=False,
                      help="delete the task file if it becomes empty")
    parser.add_option_group(config)

    output = OptionGroup(parser, "Output Options")
    output.add_option("-g", "--grep", dest="grep", default='',
                      help="print only tasks that contain WORD", metavar="WORD")
    output.add_option("-v", "--verbose",
                      action="store_true", dest="verbose", default=False,
                      help="print more detailed output (full task ids, etc)")
    output.add_option("-q", "--quiet",
                      action="store_true", dest="quiet", default=False,
                      help="print less detailed output (no task ids, etc)")
    output.add_option("--done",
                      action="store_true", dest="done", default=False,
                      help="list done tasks instead of unfinished ones")
    parser.add_option_group(output)

    return parser

def _main():
    """Run the command-line interface."""
    (options, args) = _build_parser().parse_args()

    td = TaskDict(taskdir=options.taskdir, name=options.name)
    text = ' '.join(args).strip()

    if '\n' in text:
        _die('task text cannot contain newlines')

    try:
        if options.finish:
            td.finish_task(options.finish)
            td.write(options.delete)
        elif options.remove:
            td.remove_task(options.remove)
            td.write(options.delete)
        elif options.edit:
            td.edit_task(options.edit, text)
            td.write(options.delete)
        elif text:
            td.add_task(text, verbose=options.verbose, quiet=options.quiet)
            td.write(options.delete)
        else:
            kind = 'tasks' if not options.done else 'done'
            td.print_list(kind=kind, verbose=options.verbose, quiet=options.quiet,
                          grep=options.grep)
    except AmbiguousPrefix:
        e = sys.exc_info()[1]
        _die('the ID "%s" matches more than one task' % e.prefix)
    except UnknownPrefix:
        e = sys.exc_info()[1]
        _die('the ID "%s" does not match any task' % e.prefix)
    except BadFile as e:
        _die('%s - %s' % (e.problem, e.path))

_id_counter = 62**2

if __name__ == '__main__':
    _main()
