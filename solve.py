#!/usr/bin/env python3
#
# todo: detect when *we* have no surviving moves.

import _pickle as cP
import codecs
import copy
import sqlite3 as db
import sys

#from copy import deepcopy
def deepcopy(twod): # faster
  return [x[:] for x in twod]

DEPTH = 2        # minmax depth. 2 is good unless you have a lot of time
CUTOFF = 2       # ignore words shorter than this
SPEEDCAP = 50    # consider the X longest words per position
JOKER_OFFSET = 4 # use jokers with word minimum length #

NOBODY = 0
US     = 1
THEM   = 2
BOTH   = 3
OK     = 10

HIGHLIGHT  = '\033[1;33;41m'
RED    = '\033[1;30;43m'
BLUE   = '\033[1;37;44m'
MORELIGHT  = '\033[1;33;42m'
BLACK  = '\033[0;37;40m'
GRAY   = '\033[0;36;40m'
#MORELIGHT  = '\033[1;36;41m'
DANGER = '\033[1;31;43m'
NORMAL = '\033[0m'

NP_HIT_SCORE = 2
NP_SCORE     = 10
LOTS         = 1000000

lang = "dict/twl"

nope, infile = sys.argv[0:2]
played       = [p.upper() for p in sys.argv[2:]]
played_      = [p.split("#")[:1][0] for p in played] 
played_d     = dict((x,True) for x in played_)

conn = db.connect("{}.sqlite".format(lang))
c    = conn.cursor()

c.execute("select count(word) from words")
dictlen = int(c.fetchone()[0])

lines   = [line.strip() for line in codecs.open("games/"+infile,'r','utf-8').read().strip().split("\n")]
letters = [line.upper() for line in lines]
sizex   = len(letters[0])
sizey   = len(letters)



words     = [[{} for x in range(sizex)] for y in range(sizey)]
score     = [[0 for x in range(sizex)] for y in range(sizey)]
owned     = [[NOBODY for x in range(sizex)] for y in range(sizey)]
np        = [[NOBODY for x in range(sizex)] for y in range(sizey)]
bombs     = [[letter.isupper() for letter in line] for line in lines]

wordindex = {}
attacks   = {}
threats   = {}

for x in range(sizex):
  owned[0][x] = US
  owned[sizey-1][x] = THEM

def putword(root, chain):
  global wordindex
  wordindex[root] = wordindex.get(root,[]) + [chain]

def getword(root):
  global wordindex
  return wordindex.get(root,[]) 

def beginable(root):
  c.execute("select * from lastbits where bit = '{}' limit 1".format(root))
  return c.fetchone() and True or False

ccache = {}
def ccont(root):
    if not root in ccache:
        ccache[root]=continuable(root)
    return ccache[root]

def continuable(root):
  if root[-1]=="_" and len(root)>=JOKER_OFFSET:
    root_=root[:-1]
    c.execute("select * from bits where bit > '{}' and bit <= '{}Z' and length(bit)={}".format(root_,root_,len(root)))
  else:
    c.execute("select * from bits where bit = '{}' limit 1".format(root))
  result = c.fetchall()
  return result and [x[1] for x in result]

def exists(root):
  if len(root)>12: 
      return False
  c.execute("select * from words where word = '{}' limit 1".format(root))
  return c.fetchone() and True or False

def resolve(root):
  c.execute("select * from words where word like '{}' limit 1".format(root))
  return c.fetchone()[1]

def towards (y, x, root, chain):
  if (y,x) in chain: return []
  if not beginable(root): return []
  chain = chain + [(y,x)] 

  found = []
  for dx in [-1,0,1]:
    for dy in [-1,0,1]:
      nx = x+dx
      ny = y+dy
      if (ny<0) or (nx<0) or (ny>=sizey) or (nx>=sizex):
        continue
      else:
        found = towards(ny, nx, letters[ny][nx]+root, chain)

  if exists(root):
    return [(root, chain)]+found
  else:
    return found    


def startsat (y, x, root, chain, np_cb):
  if (y,x) in chain: return []
  chain = chain + [(y,x)] 


  found = []
  for dx in [-1,0,1]:
    for dy in [-1,0,1]:
      nx = x+dx
      ny = y+dy
      if (ny<0) or (nx<0) or (ny>=sizey) or (nx>=sizex):
        continue
      else: 
        ends = ccont(root)
        for end in ends:
            found = found + startsat(ny, nx, end + letters[ny][nx], chain, np_cb)

  if exists(root):
    putword(root, chain)
    if root in played_d:
      return found
    if np_cb:
      sy, sx = chain[0]
      for ly,lx in chain:
        if ly==0:
          np_cb(root,chain,US,sy,sx)
        elif ly==sizey-1:
          np_cb(root,chain,THEM,sy,sx)
    return [(root, chain)]+found
  else:
    return found    

def register_np(root, chain, direction, y, x):
  global np
  np[y][x] = np[y][x] | direction
  if direction==THEM:
    attacks[y] = attacks.get(y,[]) + [root]
  if direction==US:
    threats[y] = threats.get(y,[]) + [root]

# preparation
# 1 opt) identify neuralgic points 
# 2) calculate letter values
#      as number of words that can be built + 10x attacks towards neuralgic points (own or opposite)

restored = False
try:
  dump = open("games/{}.idx".format(infile), "rb").read()
  letters_, words_, score_, wordindex_, attacks_, threats_, np_, dictlen_ = cP.loads(dump)
  if letters_==letters:
    print("Word list restored from dump. yay.")
    if dictlen != dictlen_:
        print("Dictionary has changed, not using dump.")
        raise Exception()
    words, score, wordindex, attacks, threats, np = words_, score_, wordindex_, attacks_, threats_, np_
    restored = True
  else:
    print("Letters have changed, not using dump.")
except Exception as e:
  print(e)
  print("Generating word index and attack vectors.")
  pass

if not restored:
  complete = sizex * sizey
  progress = 0
  for y in range(sizey):
    for x in range(sizex):
      words[y][x] = startsat(y,x,letters[y][x],[],register_np)
      words[y][x] = sorted(words[y][x], key=lambda x:len(x[0]), reverse=True)
      score[y][x] = len(words[y][x])

      progress += 1
      print("DETECTING WORDS: {:.1f}%".format(float(progress)*100/complete), end='\r')

  #add up to [NP_HIT_SCORE * distance to base] points for every NP hit
  for y in range(sizey):
    for x in range(sizex):
      for word,chain in words[y][x]:
        for ly,lx in chain:
          if np[ly][lx]:
            distance = sizey # BOTH sides' np is reached
            if np[ly][lx] == US:
              distance = y
            elif np[ly][lx] == THEM:
              distance = sizey-y
            elif np[ly][lx] == BOTH:
              distance = sizey 
            score[y][x] += NP_HIT_SCORE * distance
      if np[y][x]:
        distance = sizey # BOTH sides' np
        if np[y][x] == US:
          distance = y
        if np[y][x] == THEM:
          distance = sizey-y
        score[y][x] += NP_SCORE * distance
  
  for x in range(sizex):
    score[0][x] = LOTS
    score[sizey-1][x] = LOTS

  # create a dump of the data structures - speedup for next run on the same table
  #
  dump = open("games/{}.idx".format(infile), "wb") 
  dump.write(cP.dumps((letters, words, score, wordindex, attacks, threats, np, dictlen)))
  dump.close()

# minmax
# for all occupied letters
#  for all words we consider
#   calculate board value as [np occupied = inf/-inf, attacks to np +/- * 10, letter value]
#   where letter value is number of words starting with letter 
 
def spread(nodes, consistent, playing): # this method is super inefficient
  while len(nodes)>0:   
    y,x = nodes.pop()
    for dx in [-1,0,1]:
      for dy in [-1,0,1]:
        nx = x+dx
        ny = y+dy
        if (ny<0) or (nx<0) or (ny>=sizey) or (nx>=sizex):
          continue
        if consistent[ny][nx] == playing:
          consistent[ny][nx] = OK
          nodes.append((ny,nx)) 

def bomb(y,x,owned,bombs,playing):
  value = 0
  if bombs[y][x]:
    bombs[y][x]=False
    for ny in [y,y-1,y+1]:
      if (ny>=0) and (ny<sizey):
        value += bomb(ny,x,owned,bombs,playing)
    for nx in [x,x-1,x+1]:
      if (nx>=0) and (nx<sizex):
        value += bomb(y,nx,owned,bombs,playing)
  else:
    if owned[y][x] == NOBODY:
      value = score[y][x]
    if owned[y][x] == BOTH-playing:
      value = 2 * score[y][x]
    owned[y][x]=playing
  return value
    

def consistency(owned):
  consistent = deepcopy(owned)
  
  consistent[0][0] = OK
  spread([(0,0)], consistent, US)

  consistent[sizey-1][0] = OK
  spread([(sizey-1,0)], consistent, THEM)

  cuts = []
  for y in range(sizey):
    for x in range(sizex):
      if consistent[y][x] and not consistent[y][x]==OK:
        cuts.append((y,x))
  return cuts

def board_value(owned):
  vsum = 0
  for y in range(sizey):
    for x in range(sizex):
      if owned[y][x] == US:
        vsum += score[y][x]
      if owned[y][x] == THEM:
        vsum -= score[y][x]
  return vsum

LEGEND={
        0: " | "+RED        +"THEM       ",
        1: " | "+BLUE       +"US         ",
        2: " | "+HIGHLIGHT  +"OUR MOVE   ",
        3: " | "+MORELIGHT  +"ATTACK     ",
        4: " | "+RED        +"THEIR MOVE ",
        5: " | "+DANGER     +"THREAT     ",
        }

def printboard(owned, highlight, np):
  for y in range(sizey):
    for x in range(sizex):
      if highlight and ((y,x) in highlight):
        if np[y][x] & THEM:
          print(MORELIGHT+letters[y][x],end=' ')
        else:
          print(HIGHLIGHT+letters[y][x],end=' ')
      elif owned[y][x] == THEM:
        if np[y][x] & US:
          print(DANGER+letters[y][x],end=' ')
        else:
          print(RED+letters[y][x],end=' ')
      elif owned[y][x] == US:
        print(BLUE+letters[y][x],end=' ')
      elif np[y][x]:
        print(GRAY+letters[y][x],end=' ')
      else:
        print(BLACK+letters[y][x],end=' ')
    print(NORMAL,end='') 
    print(LEGEND.get(y,' | '),end='')
    print(NORMAL) 

  print(NORMAL)

def joker_check(jokers, chain, word):
  failed = False
  #print("JOKER CHECK",word)
  for i,(y,x) in enumerate(chain):
    joke = jokers.get((y,x)) 
    letter = word[i]
    if joke and joke != "_" and joke != letter:
      #print("FAILED", joke, "!=", letter, "in", word, "at", (y,x), "index", i, chain)
      return False
  return True

print("COMPLEXITY: {} words".format(len(wordindex)))
SPEEDCAP = int( 2500000 / len(wordindex))
print("Using a cap of {} words".format(SPEEDCAP))
jokers = {(y,x):"_" for y in range(sizey) for x in range(sizex) if letters[y][x]=="_"}

def minmax(depth, owned, jokers, reverse=False, moves=[]):
  us, them = US, THEM
  if reverse:
    us, them = THEM, US

  best = (-LOTS,None,None,None)
  rest = [] 

  moves_d = dict((x,True) for x in moves)

  loopgen = range(sizey) if reverse else range(sizey-1,-1,-1)

  if depth==DEPTH:
    num_owned = sum([x==us for y in owned for x in y])
    progress = 0
    complete = sizex * sizey

  for y in loopgen:
    for x in range(sizex):
      if owned[y][x] == us:

        if depth==DEPTH:
          progress += 1
          options = len(words[y][x][:SPEEDCAP])
          print("PROGRESS: {:.1f}% - 0/{} options       ".format(float(progress)*100/num_owned, options), end='\r')
          progress2 = 0

        for word,chain in words[y][x][:SPEEDCAP]:

          if depth==DEPTH:
            progress2 += 1
            print("PROGRESS: {:.1f}% - {}/{} options    ".format(float(progress)*100/num_owned + float(progress2)/options, progress2, options), end='\r')
          if len(word)<CUTOFF: continue  # FIXME confirm speedup?
          if word in moves_d: continue   # keep track of previous moves 
          rel_value = 0
          final = False
          for ly,lx in chain[1:]:
            if ((them == THEM) and ly == sizey-1) or ((them == US) and ly == 0):
              final = True
              rel_value = LOTS#sys.maxint
              #if depth==2:
              #  print ("CHECK final move is {} {}, best is {} {}".format(LOTS, word, best[0], best[1]))
              break
            if owned[ly][lx] == NOBODY:
              rel_value += score[ly][lx]
            if owned[ly][lx] == them:
              rel_value += 2 * score[ly][lx]
          # if depth > 0 check reverse
          opposite_move = None
          if depth>0 and rel_value>best[0] and not final:
            new_owned = deepcopy(owned)
            new_bombs = deepcopy(bombs)
            for ly,lx in chain:
              bomb(ly,lx,new_owned,new_bombs,us)
              cuts = consistency(new_owned)
              for cy,cx in cuts:
                new_owned[cy][cx] = NOBODY 
                if new_owned[cy][cx] == them:
                  rel_value += score[cy][cx] 
            opposite_move = minmax(depth-1, new_owned, copy.deepcopy(jokers), not reverse, moves + [word])

            rel_value -= opposite_move[0]
          if rel_value >= best[0]: # later words are better, because they are shorter
            #if depth==2 and not joker_check(jokers, chain, word): continue
            rest = [best] + rest
            best = (rel_value, word, chain, opposite_move)
  
  return best

def playout(play, playing, jokers, selected=-1, variant=-1):
  global owned

  if play == "-": return

  chain = None
  if variant==-1:
    chains = [c for c in getword(play) if (owned[c[0][0]][c[0][1]] == playing)]
    if not chains:
      if exists(play):
        print("Cannot play '{}' at this stage of the game.".format(play))
        switched = [c for c in getword(play) if (owned[c[0][0]][c[0][1]] == BOTH-playing)]
        if switched:
          print("Hint: The word is playable for the other player. Maybe you skipped a move.")
      else:
        print("'{}' is not in my dictionary, use addword.py to remedy this.".format(play))
      sys.exit(1) 
    matched = False
    if len(chains)>1:
      if selected==-1:
        print("{} variants to play {}. Append # + number to select.".format(len(chains), play))
        for i,chain in enumerate(chains):
          cscore = 0
          print("{}: ".format(i), end='')
          for j,position in enumerate(chain):
            cscore += score[position[0]][position[1]]
            if i>0 and chains[i-1][j] == position:
              print("   --    | ", end='')
            else:
              space=' '
              if position[0]>9: 
                  space = '';
              print(" {}{} | ".format(position,space), end='')
          print(" value {}".format(cscore), end='')
          print()
        sys.exit(1)

    try:
      chain = chains[selected]
    except: 
      print("CHAIN INDEX INVALID")
      print("{} variants to play {}. Append # + number to select.".format(len(chains), play))
      for i,chain in enumerate(chains):
        print(i, chain)
      sys.exit(1)
  else:
    chain = getword(play)[variant]
  sy,sx = chain[0]
  if owned[sy][sx] == playing:
    matched = True
    for i,(ly,lx) in enumerate(chain):
      owned[ly][lx] = playing

      # update jokers
      letter = play[i]
      joker  = jokers.get((ly,lx))
      if joker=="_":
          jokers[(ly,lx)]=letter
      elif joker is not None and joker != letter:
          print("REUSED JOKER WITH A DIFFERENT LETTER", (ly,lx), joker, "!=", letter, play)
          #sys.exit(1)

      #bomb(ly,lx,owned,bombs,playing) 
      cuts = consistency(owned)
      for cy,cx in cuts:
        owned[cy][cx] = NOBODY 
  if not matched:
    print("NOT MATCHED: '{}'".format(play))
    sys.exit(1)


playing = US
if played:
  for play in played:
    if "#" in play:
      word,variant = play.split("#") 
      if not variant:
        continue
      playout(word, playing, jokers, int(variant))
    else:
      playout(play, playing, jokers)
    playing = BOTH - playing

print("ATTACKS ===")
for depth in sorted(attacks.keys())[:1]:
  print(depth, attacks[depth])
for depth in sorted(attacks.keys())[1:3]:
  a = attacks[depth]
  if len(a)>10:
    print (depth, "{} attacks from letters {}".format(len(a), "-".join(set([w[0] for w in a]))))
  else:
    print(depth, a)
print("THREATS ===")
for depth in sorted(threats.keys())[-3:]:
  t = threats[depth]
  if len(t)>10:
    print (depth, "{} attacks from letters {}".format(len(t), "-".join(set([w[0] for w in t]))))
  else:
    print (depth, t)

print("PLAYS ===")

round = 0
if playing==THEM:
  future = minmax(DEPTH, owned, jokers, reverse=True, moves=played_)
  if not future[3]:
    print(future)
  else:
    rating, theirs, ours, ourrating = future[0], future[1], future[3][1], future[3][0]
    print ("!!!", theirs, ours, "->", ourrating)
  sys.exit(1) #quick hack to see best opp move at a glance

moves = played_
while True:
  future = minmax(DEPTH, owned, jokers, moves=moves)
  rating, ours, ourchain, th = future[0], future[1], future[2], future[3]
  if not th or not th[2]:
    printboard (owned, ourchain, np)
    print("{} - no surviving move.".format(resolve(ours)))
    final = minmax(0, owned, jokers)
    print(resolve(final[1]))
    sys.exit(1)
    break
  else:
    theirs, theirchain = th[1], th[2]
    if round==0:
      printboard(owned, ourchain, np)
    playout (ours, US, jokers, variant = wordindex[ours].index(ourchain)) 
    moves += [ours]
    warning = len(wordindex[ours]) > 1 and future[2] or ""
    print(rating, resolve(ours), theirs, warning)
    playout (theirs, THEM, jokers, variant=wordindex[theirs].index(theirchain))
    moves += [theirs]
    round += 2

