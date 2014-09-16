#!/usr/bin/env python

import sys
import sqlite3 as db
import codecs
from copy import deepcopy

sy,sx,ty,tx=0,0,0,0
nope, lang, infile = sys.argv[0:3]
if len(sys.argv)>3:
  sy, sx = [int(x) for x in sys.argv[3:5]]
if len(sys.argv)>5:
  ty, tx = [int(x) for x in sys.argv[5:7]]

conn = db.connect("%s.sqlite" % lang)
c    = conn.cursor()

letters = [line.strip() for line in codecs.open(infile,'r','utf-8').read().strip().upper().split("\n")]
sizex   = len(letters[0])
sizey   = len(letters)
print sizex,sizey
used      = [[False for x in xrange(sizex)] for y in xrange(sizey)]
reachable = [[False for x in xrange(sizex)] for y in xrange(sizey)]

longest = (0,[""])
deepest = (0,[""])

def continuable(root):
  c.execute('select * from bits where bit = "%s" limit 1' % root)
  return c.fetchone() and True or False

def exists(root):
  c.execute('select * from words where word = "%s" limit 1' % root)
  return c.fetchone() and True or False

def expand (y, x, root, used):
  global longest, deepest 

  if used[y][x]: return
  if not continuable(root) and not exists(root): return
  used[y][x] = True
  if exists(root):
    reachable[y][x] = True 
    if (not ty and not tx) or (used[ty][tx]):
      if len(root) > longest[0]:
        longest=(len(root),[root])
      if len(root) == longest[0]:
        longest=(len(root), longest[1] + [root])
      if y > deepest[0]:
        deepest=(y,[root])
      if y == deepest[0]:
        deepest=(y, deepest[1] + [root])
  for dx in [-1,0,1]:
    for dy in [-1,0,1]:
      nx = x+dx
      ny = y+dy
      if (ny<0) or (nx<0) or (ny>=sizey) or (nx>=sizex):
        continue
      else:
        expand(ny, nx, root+letters[ny][nx],used)
  used[y][x] = False

if sx or sy:
  words = expand(sy,sx,letters[sy][sx],used)
else:
  for x,start in enumerate(letters[0]):
    y = 0 
    expand(y,x,letters[y][x],used) 

print "longest", longest
print "deepest", deepest

if deepest[0] == sizey - 1: 
  print "YOU WIN"
  sys.exit(0)

# level 2 analysis
reached = deepcopy(reachable)
for y2 in xrange(0,sizey):
  for x2 in xrange(0,sizex):
    if reached[y2][x2]:
      expand(y2,x2, letters[y2][x2], used)

print "LEVEL 2"
print "longest", longest
print "deepest", deepest

if deepest[0] == sizey - 1: 
  print "YOU WIN"
  sys.exit(0)

# level 3 analysis
reached = deepcopy(reachable)
for y2 in xrange(0,sizey):
  for x2 in xrange(0,sizex):
    if reached[y2][x2]:
      expand(y2,x2, letters[y2][x2], used)

print "LEVEL 3"
print "longest", longest
print "deepest", deepest

if deepest[0] == sizey - 1: 
  print "YOU WIN"
