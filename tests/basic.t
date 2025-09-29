Setup:

  $ alias xt="python $TESTDIR/../t.py --task-dir `pwd` --list test"

Adding tasks:

  $ xt
  $ xt Sample one.
  1
  $ xt
  1 - Sample one.
  $ xt Sample two.
  2
  $ xt
  1 - Sample one.
  2 - Sample two.
  $ xt 'this | that'
  3
  $ xt
  1 - Sample one.
  2 - Sample two.
  3 - this | that

Finishing tasks:

  $ xt -f 1
  $ xt
  2 - Sample two.
  3 - this | that
  $ xt -f 2
  $ xt
  3 - this | that
  $ xt -f 3
  $ xt

Output when adding in various modes:

  $ xt foo
  4
  $ xt -v bar
  5
  $ xt -q baz
