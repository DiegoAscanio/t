Setup:

  $ alias xt="python $TESTDIR/../t.py --task-dir `pwd` --list test"

Add some tasks:

  $ xt Sample one.
  1
  $ xt Sample two.
  2
  $ xt Sample three.
  3
  $ xt Sample four.
  4
  $ xt 'this | that'
  5

Finish and test .test.done:

  $ xt -f 1
  $ cat .test.done
  Sample one. | id:1
  $ xt -f 2
  $ cat .test.done
  Sample one. | id:1
  Sample two. | id:2
  $ xt -f 3
  $ cat .test.done
  Sample one. | id:1
  Sample two. | id:2
  Sample three. | id:3
  $ xt -f 4
  $ cat .test.done
  Sample one. | id:1
  Sample two. | id:2
  Sample three. | id:3
  Sample four. | id:4
  $ xt -f 5
  $ cat .test.done
  Sample one. | id:1
  Sample two. | id:2
  Sample three. | id:3
  Sample four. | id:4
  this | that | id:5
