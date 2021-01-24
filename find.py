#!/usr/bin/env python3
#
# todo: detect when *we* have no surviving moves.

import sys
import sqlite3 as db
import codecs
import _pickle as cP

#from copy import deepcopy
def deepcopy(twod): # faster
  return [x[:] for x in twod]

CUTOFF = 2 # ignore words shorter than this

NOBODY = 0
US     = 1
THEM   = 2
BOTH   = 3
OK     = 10

HIGHLIGHT  = '\033[1;33;41m'
RED    = '\033[1;30;43m'
BLUE   = '\033[1;37;44m'
BLACK  = '\033[0;37;40m'
GRAY   = '\033[0;36;40m'
MORELIGHT  = '\033[1;36;41m'
DANGER = '\033[1;31;43m'
NORMAL = '\033[0m'

NP_HIT_SCORE = 2
NP_SCORE     = 10
LOTS         = 100000

lang = "dict/twl"

nope, infile, searchx, searchy = sys.argv[0:4]
played       = [p.upper() for p in sys.argv[4:]]
played_      = [p.split("#")[:1][0] for p in played] 
played_d     = dict((x,True) for x in played_)

conn = db.connect("%s.sqlite" % lang)
c    = conn.cursor()

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
  c.execute('select * from lastbits where bit = "%s" limit 1' % root)
  return c.fetchone() and True or False

ccache = {}
def ccont(root):
    if not root in ccache:
        ccache[root]=continuable(root)
    return ccache[root]

def continuable(root):
  if root[-1]=="_" and len(root)>=2:
    c.execute('select * from bits where bit > "%s" and bit <= "%s" and length(bit)=%i' % (root[:-1],root[:-1]+'Z',len(root)))
  else:
    c.execute('select * from bits where bit = "%s" limit 1' % root)
  result = c.fetchall()
  return result and [x[1] for x in result]

def exists(root):
  if len(root)>12: 
      return False
  c.execute('select * from words where word = "%s" limit 1' % root)
  return c.fetchone() and True or False

def resolve(root):
  c.execute('select * from words where word like "%s" limit 1' % root)
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
  dump = open("games/%s.idx" % infile, "rb").read()
  letters_, words_, score_, wordindex_, attacks_, threats_, np_ = cP.loads(dump)
  if letters_==letters:
    words, score, wordindex, attacks, threats, np = words_, score_, wordindex_, attacks_, threats_, np_
    restored = True
    print("Word list restored from dump. yay.")
  else:
    print("Letters have changed, not using dump.")
except:
  print("Generating word index and attack vectors.")
  print(sys.exc_info())
  pass

if not restored:
  for y in range(sizey):
    for x in range(sizex):
      words[y][x] = startsat(y,x,letters[y][x],[],register_np)
      words[y][x] = sorted(words[y][x], key=lambda x:len(x[0]), reverse=True)
      score[y][x] = len(words[y][x])

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
  dump = open("games/%s.idx" % infile, "wb") 
  dump.write(cP.dumps((letters, words, score, wordindex, attacks, threats, np)))
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
    print(NORMAL) 
  print(NORMAL)

def minmax(depth, owned, reverse=False, moves=[]):
  us, them = US, THEM
  if reverse:
    us, them = THEM, US

  best = (-LOTS,None,None,None)
  rest = [] 

  moves_d = dict((x,True) for x in moves)

  loopgen = range(sizey) if reverse else range(sizey-1,-1,-1)
  # iterate over the stronger (closer) moves first
  #for y in range(sizey-1,-1,-1):
  #for y in range(sizey):
  for y in loopgen:
    for x in range(sizex):
      if owned[y][x] == us:
        for word,chain in words[y][x]:
          if len(word)<CUTOFF: continue  # FIXME confirm speedup?
          if word in moves_d: continue   # keep track of previous moves 
          rel_value = 0
          final = False
          for ly,lx in chain[1:]:
            if ((them == THEM) and ly == sizey-1) or ((them == US) and ly == 0):
              final = True
              rel_value = LOTS#sys.maxint
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
            opposite_move = minmax(depth-1, new_owned, not reverse, moves + [word])

            rel_value -= opposite_move[0]
          if rel_value > best[0]:
            rest = [best] + rest[:4]
            best = (rel_value, word, chain, opposite_move)
  
  return best

def playout(play, playing, selected=-1, variant=-1):
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
          print(i, chain)
        sys.exit(1)
    chain = chains[selected]
  else:
    chain = getword(play)[variant]
  sy,sx = chain[0]
  if owned[sy][sx] == playing:
    matched = True
    for ly,lx in chain:
      owned[ly][lx] = playing
      bomb(ly,lx,owned,bombs,playing) 
      cuts = consistency(owned)
      for cy,cx in cuts:
        owned[cy][cx] = NOBODY 
  if not matched:
    print("NOT MATCHED: '{}'".format(play))

print("COMPLEXITY: {} words".format(len(wordindex)))

playing = US
if played:
  for play in played:
    if "#" in play:
      word,variant = play.split("#") 
      if not variant:
        continue
      playout(word, playing, int(variant))
    else:
      playout(play, playing)
    playing = BOTH - playing

print("ATTACKS ===")
for depth in sorted(attacks.keys())[:1]:
  print(depth, attacks[depth])
for depth in sorted(attacks.keys())[1:3]:
  a = attacks[depth]
  #if len(a)>10:
  #  print depth, "%i attacks" % len(a)
  #else:
  print(depth, a)
print("THREATS ===")
for depth in sorted(threats.keys())[-3:]:
  t = threats[depth]
  if len(t)>10:
    print (depth, "{} attacks".format(len(t)))
  else:
    print (depth, t)

searchx = int(searchx)
searchy = int(searchy)
print ("WORDS {} {} ===".format(searchx,searchy))

def deepest(x):
    return x[1][-1][0]
    #return x[1][-1][1]

w = sorted(words[searchy][searchx],key=deepest)
for x in w[0:30]:
    print(x)

print("REVERSE {} {} ===".format(searchx,searchy))
w = sorted(words[searchy][searchx],key=deepest,reverse=True)
for x in w[0:40]:
    print(x)
