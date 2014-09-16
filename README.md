wordbase-solver
===============

A three step minmax solver for wordbase-like games.


Installation 
------------

Just clone and run. 

Python module requirements: sqlite3


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
    
    
    







