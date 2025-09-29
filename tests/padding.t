Setup:

  $ alias xt="python $TESTDIR/../t.py --task-dir `pwd` --list test"

Add tasks of varying width:

  $ xt Short.
  1
  $ xt Longcat is long.
  2

Test paddings:

  $ xt
  1 - Short.
  2 - Longcat is long.
  $ cat test
  Short. | id:1
  Longcat is long. | id:2
  $ cat >> test << EOF
  > Long one. | id: long1
  > Very long two. | id: long2
  > EOF
  $ xt -f 1
  $ xt
  2     - Longcat is long.
  long1 - Long one.
  long2 - Very long two.
  $ cat test
  Longcat is long. | id:2
  Long one. | id:long1
  Very long two. | id:long2
