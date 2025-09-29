Setup:

  $ alias xt="python $TESTDIR/../t.py --task-dir `pwd` --list test"

Add a task file:

  $ ls -a
  .
  ..
  $ xt
  $ ls -a
  .
  ..
  $ xt Sample.
  1
  $ ls -a
  .
  ..
  .test.done
  test

Finish a task without deleting:

  $ xt -f 1
  $ ls -a
  .
  ..
  .test.done
  test

Finish a task with deleting:

  $ xt Another.
  2
  $ xt --delete-if-empty -f 2
  $ ls -a
  .
  ..
  .test.done

