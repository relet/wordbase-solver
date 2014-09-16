#!/usr/bin/env python

import sys
import sqlite3 as db

nope, outdb, word = sys.argv
conn = db.connect("%s.sqlite" % outdb)
c = conn.cursor()

word = word.strip().upper()
c.execute('delete from words where word = "%s"' % word)

conn.commit()
