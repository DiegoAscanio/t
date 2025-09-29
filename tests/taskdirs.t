Setup:

  $ alias xt="python $TESTDIR/../t.py --list test"

Initialize multiple task directories:

  $ mkdir beer
  $ mkdir books
  $ xt --task-dir beer Dogfish Head 120 minute IPA
  1
  $ xt --task-dir books Your Inner Fish
  1
  $ xt --task-dir beer
  1 - Dogfish Head 120 minute IPA
  $ xt --task-dir books
  1 - Your Inner Fish

Wrong directories:

  $ xt --task-dir beer -f 0
  error: the ID "0" does not match any task
  [1]
  $ xt --task-dir books -f 7
  error: the ID "7" does not match any task
  [1]
  $ xt --task-dir beer
  1 - Dogfish Head 120 minute IPA
  $ xt --task-dir books
  1 - Your Inner Fish

Right directories:

  $ xt --task-dir beer -f 1
  $ xt --task-dir books -f 1
  $ xt --task-dir beer
  $ xt --task-dir books

