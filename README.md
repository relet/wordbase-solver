wordbase-solver
===============

A fast three step minmax solver for wordbase-like games.


Installation 
------------

Just clone and run. 

    git clone https://github.com/relet/wordbase-solver.git
    cd wordbase-solver
    ./solve.py gamefile

Requires a python interpreter and the following modules: sqlite3


Usage
-----

The solver requires you to create a two dimensional text field in the games/ directory that describes your initial game board. Examples can be found in the games/ directory. If you are the first player, just copy your game board as is, using small letters for regular letters, and capital letters for bomb tiles. **If you are the second player, reverse the board starting with the lowest line.** For the sake of simplicity, the solver always assumes that you are playing towards the bottom end of the board. 

You can then start the solver, and optionally provide the previously played moves. 

    ./solve.py example1 [moves]
    
This will start the solver, assuming you are the red player looking for a move. Upon first analyzing a board, you will get the message

    Generating word index and attack vectors.
    
The solver looks up all possible moves and stores these in an index file (games/example1.idx) for quick lookup.

After this process is finished, it will display the longest attacks you can play, and the longest threats. See section "Analysis" for a description of these terms. 

After a moment of thinking, it will then present you with an ANSI-colored display of the best move found (if your terminal does not support ANSI it may look odd). It will also display one or several lines like this:

    27174 SPONSAL DENOMINAL [(0, 3), (1, 4), (2, 5), (3, 5), (3, 6), (4, 6), (4, 5)]
    
This is essentially the summary of the analysis. 

- The first number is the scoring of this move. If it increases, you are gainging in dominance on the board. If it decreases, you are losing dominance of the board. 
- The first word is your best move. 
- The second word is the best counter move the opponent can play, based on the remaining steps of the minmax analysis. This may vary if you actually run the more detailed three-step analysis for the opponent.
- If you get a list of coordinates, this means that your word may be played in various ways on the board. In order to help you identify the correct combination, refer to the visual board or this list. 

You may also get one of the following messages:

    RESTRAINER - no surviving move.

Which essentially means that if you play this word, you have either reached the other side of the board, or will reach the opposite side with the very next move, without a chance for the opponent to play an effective counter.

    If they play FOO you lose.
    
This is the equivalent for your opponent. There is little you can do against it, assuming they are playing a perfect game.

At the moment, the solver does not identify that you actually won the game, so it may be that it is suggesting a winning move, but still presents you with a counter. 


Pre-played moves
----------------

In order to provide the played moves, just type the words in the order in which they have been played. If you are the blue player (and the game board is reversed), the first move should be the string "-", which tells the solver that you passed a turn. 

If you provide an odd number of moves, the solver will run the analysis of the best move for your opponent. If you provide an even number of moves, the solver will run the analysis of your best next move.

So, after that first suggestion, you could want to run the full three-step analysis for your opponent.

    ./solve.py example1 SPONSAL
    
The solver replies with 

    !!! KANTARS UPFLINGS -> -7633

So, after a deeper analysis DENOMINAL was not the best move, but KANTARS is either a stronger attack, or easier to defend with. Again, the solver shows your currently best counter-attack UPFLINGS and the change in score. 

To play out that move, type:

    ./solve.py example1 sponsal kantars

And we are already fighting in the middle of the board.


Impossible moves
------------------

Sometimes, you make mistakes. The script will try to tell you what went worng:

    # ./solve.py example1 hello
    Cannot play 'HELLO' at this stage of the game.

The most common causes for this error is when you chose the wrong move from a choice of words (e.g. ESCAPERS#0 instead of ESCAPERS#1) and the move will not be possible with the chosen option.

    # ./solve.py example1 - sponsal
    Cannot play 'SPONSAL' at this stage of the game.
    Hint: The word is playable for the other player. Maybe you skipped a move.

    # ./solve.py example1 nonexist
    'NONEXIST' is not in my dictionary, use addword.py to remedy this.




Blue player
----------------

Now, let us assume that the board is reversed, and we are actually the blue player. To indicate this, start with the string "-" as first move. 

    ./solve.py example1 -
    
Again, the solver will suggest KANTARS as the best first move for the red player. You may also notice that the attacks and threats are reversed, as you are now playing the other side of the board.

The game continues with 

    ./solve.py example1 - kantars
    
    19564 BLEACHES SUBPARTS


Ambiguous moves
---------------

If a pre-played move is not unambiguous (i.e. can be played in one of several variants), the solver will ask you for clarification:

    ./solve.py example1 lens
    
    2 variants to play LENS. Append # + number to select.
    0 [(0, 7), (1, 8), (2, 7), (3, 6)]
    1 [(0, 7), (1, 8), (2, 7), (3, 8)]

Select the variant that you meant to play by appending the number sign "#" and the first number in this list to the suggested word:

    ./solve.py example1 lens#1   
    
    
Colors
------

In the ANSI-colored board display, the following colors are used:

- WHITE  on BLUE: your occupied field
- YELLOW on RED : suggested move
- CYAN   on RED : suggested move (neuralgic point!)

- CYAN on BLACK : unoccupied field - neuralgic point
- GRAY on BLACK : unoccupied field - no attacks

- GRAY on YELLOW: enemy occupied field
- RED  on YELLOW: enemy occupied field (neuralgic point!) 

    
    
Analysis
========

This solver works by assigning a score to every field of the board. The actual numbers may be set in the program.

- Fields on the base line are worth lots of points. If a player occupies these, the game ends. 
- Any field from which you can reach either base line in one move is worth many points. These are the fields you want to attack or defend. I call these *neuralgic points*. Any winning move is called an *attack* or a *threat*, depending on who is able to play it. Longer attacks from the center of the board are worth more points.
- Any field from which you can reach a neuralgic points is worth a little more than a regular field. 
- Regular fields get their score based on how many possible words start on this location. Fields which allow you to play a lot of new words are worth more points.

Based on this scoring, the wordbase-solver runs a minmax analysis. This is set to a depth of three steps (your move, opponent's counter, your best counter) which runs fine on a regular desktop machine. If you have access to a better computer, or manage to optimize the code, you can increase the number of steps. 



Utilities and Dictionaries
==========================

The repository currently includes two dictionaries.

- *twl* is the TWL06 scrabble word list. This one seems to be a good enough match with the internal wordbase dictionary for English. Of course, we can only guess.
- *no* is a Norwegian word list based on "NSF-ordlisten". Again, a reasonable match. 
 
Should you find that a word is not in the dictionary, or a word is suggested by the solver but not recognized by wordbase, you can edit your local copy of the wordlist with the following utilities. *Remember to delete the game's .idx file in order to re-analyze the possible moves* before you run the solver again.

addword.py
----------

    ./addword.py dict/twl newword
    
Adds a word to the word list.

rmword.py
----------

    ./rmword.py dict/twl notrecognized
    
Removes a word from the word list.

find.py
----------

This is essentially an earlier, more simplistic one step solver. It just reads a board file, and provides you with both the longest and deepest words found (and continues that for two more steps, which are rather useless). It has a few filtering options which may be interesting if you want to analyze a game manually.

    ./find.py dict/twl games/game [coordinates] [target]
    
It does not yet assume that dictionaries be in the dict/ folder or games in the games/ folder, so you'll have to provide the full path. 

- coordinates are two parameters which filter where to begin the word. If provided, only words starting at that coordinate will be shown.
- target are two parameters which filter which field should be hit by the word. If provided, only words that hit a given field will be shown. If you want to provide a target but no start coordinates, set the start coordinates to "0 0".

Examples:

    # best words from base
    ./find.py dict/twl games/example1
    10 13
    longest (9, [u'BEAMISHLY', u'BEAMISHLY', u'IMPOSTORS', u'IMPOSTERS', u'DENTALIUM', u'DECRETALS'])
    deepest (5, [u'BEGIRD', u'BEGIRD', u'BEGIRT', u'BEGGED', u'BEHEADED', u'BEADED', u'LEGGED', u'LEADED', u'SHADED', u'IMAGED', u'IMPEDED', u'DENTALIUM'])

    # best words from field 4 5
    ./find.py dict/twl games/example1 4 5
    10 13
    longest (9, [u'LIFESPANS', u'LIFESPANS', u'LIFESPANS'])
    deepest (9, [u'LINGUAL', u'LINGUAL', u'LINGUAE', u'LINGUAL'])

    # best words from field 4 5 hitting 6 5 (not possible)
    ./find.py dict/twl games/example1 4 5 6 5
    10 13
    longest (0, [''])
    deepest (0, [''])
    
    # best words from base hitting 2 2 
    ./find.py dict/twl games/example1 0 0 2 2
    10 13
    longest (9, [u'BEAMISHLY', u'BEAMISHLY'])
    deepest (5, [u'BEHEADED', u'BEHEADED', u'BEADED', u'LEADED', u'SHADED', u'IMAGED'])



Known issues
============

- If the opponent has one strong but obscure move, the suggestions may seem to be weak. If your opponent is playing a perfect game, this is a reasonable assumption. If you are playing against humans, a strong move that only has an obscure counter may be a better strategy. 
