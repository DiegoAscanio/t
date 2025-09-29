Setup:

  $ alias xt="python $TESTDIR/../t.py --task-dir `pwd` --list test"

Make some tasks that collide in their first letter:

  $ xt 1
  1
  $ xt 2
  2
  $ xt 3
  3
  $ xt 4
  4
  $ xt 5
  5
  $ xt 6
  6
  $ xt 7
  7
  $ xt 8
  8
  $ xt 9
  9
  $ xt 10
  10
  $ xt 11
  11
  $ xt 12
  12
  $ xt 13
  13
  $ xt 14
  14
  $ xt
  1  - 1
  2  - 2
  3  - 3
  4  - 4
  5  - 5
  6  - 6
  7  - 7
  8  - 8
  9  - 9
  10 - 10
  11 - 11
  12 - 12
  13 - 13
  14 - 14

Even more ambiguity:

  $ xt 1test
  15
  $ xt 2test
  16
  $ xt 3test
  17
  $ xt 4test
  18
  $ xt 5test
  19
  $ xt 6test
  20
  $ xt 7test
  21
  $ xt 8test
  22
  $ xt 9test
  23
  $ xt 10test
  24
  $ xt 11test
  25
  $ xt 12test
  26
  $ xt 13test
  27
  $ xt 14test
  28
  $ xt
  1  - 1
  2  - 2
  3  - 3
  4  - 4
  5  - 5
  6  - 6
  7  - 7
  8  - 8
  9  - 9
  10 - 10
  11 - 11
  12 - 12
  13 - 13
  14 - 14
  15 - 1test
  16 - 2test
  17 - 3test
  18 - 4test
  19 - 5test
  20 - 6test
  21 - 7test
  22 - 8test
  23 - 9test
  24 - 10test
  25 - 11test
  26 - 12test
  27 - 13test
  28 - 14test

