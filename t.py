#!/usr/bin/env python

"""t is for people that want do things, not organize their tasks."""

from __future__ import with_statement, print_function

import os, re, sys, hashlib
from operator import itemgetter
from optparse import OptionParser, OptionGroup
from uuid_utils import uuid7, UUID
from itertools import starmap
from pdb import set_trace
import time


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

def _id():
    """Return a new unique ID chronologically sortable for a task."""
    return uuid7().hex

def _parse_text_and_metadata_from_taskline(line: str):
    text, sep, content = line.partition('|')
    return (text.strip(), content.strip()) if sep else (line.strip(), None)

def _sort_ids(p_id, c_id, n_id):
    """Return the sorted order of the given IDs, ignoring None values."""
    ids = [i for i in (p_id, c_id, n_id) if i is not None]
    ids.sort()
    return ids

def _task_based_on_neighbour_lines(c_line: str, p_line: str, n_line: str) -> tuple[dict, dict, dict]:
    def _delta_task_id(task_id : str, increase = True, next_task_id = ''):
        start = UUID(task_id)
        time.sleep(0.025) # increase difference between UUIDs
        before = UUID(_id())
        after = (UUID(_id()).int - before.int) % (1 << 32)\
                if not next_task_id else \
                (UUID(next_task_id).int - start.int) %  (1 << 32) // 2
        return UUID(
                int = start.int + (after if increase else -after)
        ).hex

    """
    Given the current, previous and next tasklines, return the current tasks
    taking into account the neighbour states.
    """
    c = _build_task(
            *_parse_text_and_metadata_from_taskline(c_line)
            )
    p = _build_task(
            *_parse_text_and_metadata_from_taskline(p_line)
            ) if p_line else dict()
    n = _build_task(
            *_parse_text_and_metadata_from_taskline(n_line)
            ) if n_line else dict()
    c_id = c.get('id', None)
    p_id = p.get('id', None)
    n_id = n.get('id', None)

    match (
            c_id is not None,
            p_id is not None,
            n_id is not None
            ):
        # None, None, None which means new task
        case [False, False, False]: 
            c['id'] = _id()
        # Has previous and next tasks with IDs, so we can generate
        # a new ID and assign it in order to current, previous and next
        # while keeping the order
        case [False, True, True]:
            c_id = _delta_task_id(
                    p_id,
                    increase=True,
                    next_task_id=n_id
            )
            p['id'], c['id'], n['id'] = _sort_ids(p_id, c_id, n_id)
        # Has previous task without ID, but current and next both have IDs
        case [True, False, True]:
            p_id = _delta_task_id(c_id, increase=False)
            p['id'], c['id'], n['id'] = _sort_ids(p_id, c_id, n_id)
        # Has next task without ID, but current and previous both have IDs
        case [True, True, False]:
            n_id = _delta_task_id(c_id, increase=True)
            p['id'], c['id'], n['id'] = _sort_ids(p_id, c_id, n_id)
        # Has only current task with ID, so we generate two new IDs.
        # from the current one, making previous smaller and next larger.
        case [True, False, False]:
            p_id = _delta_task_id(c_id, increase=False)
            n_id = _delta_task_id(c_id, increase=True)
            p['id'], c['id'], n['id'] = p_id, c_id, n_id
        # Has only previous task with ID, so we generate two new IDs.
        case [False, True, False]:
            c_id = _delta_task_id(p_id, increase=True)
            n_id = _delta_task_id(c_id, increase=True)
            p['id'], c['id'], n['id'] = p_id, c_id, n_id
        # Has only next task with ID, so we generate two new IDs.
        # from the next one, making current smaller and previous even smaller.
        case [False, False, True]:
            c_id = _delta_task_id(n_id, increase=False)
            p_id = _delta_task_id(c_id, increase=False)
            p['id'], c['id'], n['id'] = p_id, c_id, n_id
        # If everyone has IDs, we order them only to keep consistency
        case [True, True, True]:
            p['id'], c['id'], n['id'] = _sort_ids(p_id, c_id, n_id)

    return (c, p, n)

def _build_task(text, metadata = None):
    task = { 'text': text }
    if metadata:
        for piece in metadata.strip().split(','):
            label, data = piece.split(':')
            task[label.strip()] = data.strip()
    return task


def _task_from_taskline(current_line, previous_line, next_line):
    """Parse a taskline (from a task file) and return a task.

    A taskline should be in the format:

        summary text ... | meta1:meta1_value,meta2:meta2_value,...

    The task returned will be a dictionary such as:

        { 'id': <hash id>,
          'text': <summary text>,
           ... other metadata ... }

    We'll also return updated versions of current_line, previous_line
    and next_line to reflect any modifications performed to keep IDs
    consistent and ordered.

    A taskline can also consist of only summary text, in which case the id
    and other metadata will be generated when the line is read.  This is
    supported to enable editing of the taskfile with a simple text editor.
    """
    if current_line.strip().startswith('#'): # Skip comments
        return [ None ] * 4
    """
    Current task should always reflect neighbour states, so we can keep IDs
    consistent and ordered even if the taskfile is edited manually.
    """
    c, p, n = _task_based_on_neighbour_lines(
            current_line,
            previous_line,
            next_line
            )

    previous_line = _taskline_from_task(p) if 'text' in p else previous_line
    next_line = _taskline_from_task(n) if 'text' in n else next_line
    current_line = _taskline_from_task(c)

    """
        We'll also update current_line, previous_line and next_line to
        reflect any modifications possibly performed
    """
    return c, current_line, previous_line, next_line

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

def _ensure_tasklines_consistency(tls):
    """
    Ensure that after a summary line is found, all subsequent lines will
    be transformed into summary lines, so every task has a unique and 
    sortable ID.
    """
    summary_lines = list(map(_summary_line, tls))
    summary_idx = summary_lines.index(True) if True in summary_lines else -1
    if summary_idx != -1:
        for i in range(summary_idx, len(tls)):
            if not _summary_line(tls[i]):
                text, _ = _parse_text_and_metadata_from_taskline(tls[i])
                tls[i] = text
    return tls

def _handle_tasks(tls, past_shifted_tls, future_shifted_tls):
    """
    Given a list of tasklines, return the corresponding tasks.
    We'll also perform modifications to the tasklines to keep IDs consistent
    and ordered based on neighbour states.
    """ 
    tasks = []
    number_of_tasks = len(tls)
    for i in range(number_of_tasks):
        c_line = tls[i]
        p_line = past_shifted_tls[i]
        n_line = future_shifted_tls[i]
        task, c_line, p_line, n_line = _task_from_taskline(
            c_line, p_line, n_line
        )
        tls[i] = c_line
        past_shifted_tls[i] = p_line
        # bind current line to the next past shifted line
        past_shifted_tls[
            (i + 1) % number_of_tasks
        ] = c_line
        future_shifted_tls[i] = n_line
        tasks.append(task)

    return tasks, tls, past_shifted_tls, future_shifted_tls

def _task_from_taskline_simple(line, tasks_hashes_id_map):
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

def _handle_tasks_simple(tls, tasks_hashes_id_map):
    """
    Given a list of properly consistent tasklines, return the corresponding tasks.
    """
    tasks = []
    for line in tls:
        task = _task_from_taskline_simple(line, tasks_hashes_id_map)
        tasks += [task] if task not in tasks else []
    return tasks


class TaskDict(object):
    """A set of tasks, both finished and unfinished, for a given list.

    The list's files are read from disk when the TaskDict is initialized. They
    can be written back out to disk with the write() function.

    """
    def __init__(self, taskdir='.', name='tasks'):
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
                        tls = _ensure_tasklines_consistency(tls)
                        # Simple version without neighbour-based ID consistency
                        tasks = _handle_tasks_simple(
                            tls,
                            self.tasks_hashes_id_map
                        )
                        '''
                        dumb-fuckery
                        past_shifted_tls = [''] + tls[:-1]
                        future_shifted_tls = tls[1:] + ['']
                        tasks, tls, past_shifted_tls, future_shifted_tls = _handle_tasks(
                            tls,
                            past_shifted_tls,
                            future_shifted_tls
                        )
                        '''
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
        for _, task in sorted(tasks.items()):
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
            tasks = sorted(getattr(self, kind).values(), key=itemgetter('id'))
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


if __name__ == '__main__':
    _main()
