Setup:

  $ alias xt="python $TESTDIR/../t.py --task-dir `pwd` --list test"

Add some test tasks:

  $ xt Sample one.
  1
  $ xt Sample two.
  2

Bad prefix:

  $ xt -f BAD
  error: the ID "BAD" does not match any task
  [1]
  $ xt -e BAD This should not be replaced.
  error: the ID "BAD" does not match any task
  [1]
  $ xt
  1 - Sample one.
  2 - Sample two.

Ambiguous identifiers:

  $ xt 1
  3
  $ xt 2
  4
  $ xt 3
  5
  $ xt 4
  6
  $ xt 5
  7
  $ xt 6
  8
  $ xt 7
  9
  $ xt 8
  10
  $ xt 9
  11
  $ xt 10
  12
  $ xt 11
  13
  $ xt 12
  14
  $ xt 13
  15
  $ xt 14
  16
  $ xt -f 1
  $ xt -f 2
  $ xt -f 1
  error: the ID "1" matches more than one task
  [1]
  $ xt -e 1
  error: the ID "1" matches more than one task
  [1]
  $ xt -f e This should not be replaced.
  error: the ID "e" does not match any task
  [1]
  $ xt
  3  - 1
  4  - 2
  5  - 3
  6  - 4
  7  - 5
  8  - 6
  9  - 7
  10 - 8
  11 - 9
  12 - 10
  13 - 11
  14 - 12
  15 - 13
  16 - 14

Even more ambiguity:

  $ xt 1test
  17
  $ xt 2test
  18
  $ xt 3test
  19
  $ xt 4test
  2
  $ xt 5test
  21
  $ xt 6test
  22
  $ xt 7test
  23
  $ xt 8test
  24
  $ xt 9test
  25
  $ xt 10test
  26
  $ xt 11test
  27
  $ xt 12test
  28
  $ xt 13test
  29
  $ xt 14test
  30
  $ xt
  3  - 1
  4  - 2
  5  - 3
  6  - 4
  7  - 5
  8  - 6
  9  - 7
  10 - 8
  11 - 9
  12 - 10
  13 - 11
  14 - 12
  15 - 13
  16 - 14
  17 - 1test
  18 - 2test
  19 - 3test
  20 - 4test
  21 - 5test
  22 - 6test
  23 - 7test
  24 - 8test
  25 - 9test
  26 - 10test
  27 - 11test
  28 - 12test
  29 - 13test
  30 - 14test
  $ xt -f 2
  error: the ID "2" matches more than one task
  [1]
  $ xt -e 2
  error: the ID "2" matches more than one task
  [1]
  $ xt
  3  - 1
  4  - 2
  5  - 3
  6  - 4
  7  - 5
  8  - 6
  9  - 7
  10 - 8
  11 - 9
  12 - 10
  13 - 11
  14 - 12
  15 - 13
  16 - 14
  17 - 1test
  18 - 2test
  19 - 3test
  20 - 4test
  21 - 5test
  22 - 6test
  23 - 7test
  24 - 8test
  25 - 9test
  26 - 10test
  27 - 11test
  28 - 12test
  29 - 13test
  30 - 14test
