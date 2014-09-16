#!/usr/bin/env python

import sys
import sqlite3 as db

nope, outdb, word = sys.argv
conn = db.connect("%s.sqlite" % outdb)
c = conn.cursor()

word = word.strip().upper()
c.execute('insert or replace into words values (NULL,"%s")' % word)
for i in xrange(1,len(word)):
  c.execute('insert or replace into bits values (NULL,"%s")' % word[0:i])
for i in xrange(1,len(word)):
  c.execute('insert or replace into lastbits values (NULL,"%s")' % word[i:])

conn.commit()
