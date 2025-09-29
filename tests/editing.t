Setup:

  $ alias xt="python $TESTDIR/../t.py --task-dir `pwd` --list test"

Replace a task's text (preserving the ID):

  $ xt Sample.
  1
  $ xt
  1 - Sample.
  $ xt -e 1 New sample.
  $ xt
  1 - New sample.
  $ xt 'this | that'
  2
  $ xt
  1 - New sample.
  2 - this | that
  $ xt -e 2 'this &| that'
  $ xt
  1 - New sample.
  2 - this &| that

Sed-style substitution:

  $ xt -e 1 's/New/Testing/'
  $ xt
  1 - Testing sample.
  2 - this &| that
  $ xt -e 2 '/this &/this /'
  $ xt
  1 - Testing sample.
  2 - this | that

