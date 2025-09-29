Setup:

  $ alias xt="python $TESTDIR/../t.py --list `pwd`"

Initialize multiple task lists:

  $ xt --list beer Dogfish Head 120 minute IPA
  1
  $ xt --list books Your Inner Fish
  1
  $ xt --list beer
  1 - Dogfish Head 120 minute IPA
  $ xt --list books
  1 - Your Inner Fish

Wrong lists:

  $ xt --list beer -f 0
  error: the ID "0" does not match any task
  [1]
  $ xt --list books -f 7
  error: the ID "7" does not match any task
  [1]
  $ xt --list beer
  1 - Dogfish Head 120 minute IPA
  $ xt --list books
  1 - Your Inner Fish

Right lists:

  $ xt --list beer -f 1
  $ xt --list books -f 1
  $ xt --list beer
  $ xt --list books

