# -*- coding: utf-8 -*-
"""
Usage: python biblo-web.py 8079 (or another port)

Makes use of the simple web framework "web.py" http://webpy.org/ ~ https://github.com/webpy/webpy
"""
import web
import sys
import os
import shutil
import codecs
import json
from pprint import pprint

#Import bilbo
sys.path.append('..')
from bilbo.Bilbo import Bilbo
from bilbo.utils import *

urls = (
	'/', 'bilboWeb',
	'/bilbo', 'bilboWeb',
	'/annotate', 'annotate',
)

class annotate:
	def POST(self):
		i = web.input(('corpus'), texts=[])
		corpus = int(i.corpus)
		if (not corpus > 0):
			return web.webapi.BadRequest()

		mkTmp()
		cpt = 0
		for text in i.texts:
			fichier = codecs.open("tmp/in/fichier_" + str(cpt)+".xml", "w", "utf-8")
			fichier.write(text)
			fichier.close()
			cpt += 1
		
		if (cpt>0):
			annoterCorpus(corpus)
		else:
			return web.webapi.BadRequest()
		
		resultat = []
		while cpt > 0:
			cpt -= 1
			#recupere le resultat de BILBO
			fichier = codecs.open("tmp/out/fichier_" + str(cpt)+".xml", "r", "utf-8")
			resultat.append(''.join( fichier.readlines()))
			fichier.close()
		
		delTmp()

		retour = json.dumps(resultat)
		if ('callback' in i):
			retour = i.callback + '(' + retour + ')'
		
		web.header('Content-Type','application/json;')
		return retour

	def GET(self):
		return self.POST()

class bilboWeb:
	def GET(self):
		render = web.template.render('templates/')
		return render.bilbo()
	
def annoterCorpus(corpus):
	options = type('object', (), {'i':'tei', 'm':'revues', 'g':'simple', 'k':'none', 'v':'none', 'u':False, 's':False, 'o':'tei', 'd':False, 'e':False})
	dirModel = os.path.abspath('../../model/corpus' + str(corpus) + "/revues/") + "/"
	dir_in = os.path.abspath('tmp/in') + "/"
	dir_out = os.path.abspath('tmp/out') + "/"
	bilbo = Bilbo(dir_out, options, "crf_model_simple")
	bilbo.annotate(dir_in, dirModel, corpus)
	return

def mkTmp():
	try: os.mkdir('tmp/in')
	except OSError:	pass
	except:	raise
	try: os.mkdir('tmp/out')
	except OSError:	pass
	except:	raise
	
def delTmp():
	shutil.rmtree('tmp/in')
	shutil.rmtree('tmp/out')

if __name__ == "__main__":
	app = web.application(urls, globals())
	app.run()