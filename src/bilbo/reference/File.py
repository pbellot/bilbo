# -*- coding: utf-8 -*-
'''
Created on 25 avr. 2012

@author: Young-Min Kim, Jade Tavernier
'''
from bs4 import BeautifulSoup, NavigableString
from bilbo.format.Clean import Clean
from bilbo.format.CleanCorpus1 import CleanCorpus1
from bilbo.format.CleanCorpus2 import CleanCorpus2
from bilbo.format.Rule import Rule
from bilbo.reference.ListReferences import ListReferences
from bilbo.output.identifier import extractDoi, loadTEIRule, toTEI
import re
import sys

prePunc =  {'.':0, ',':0, ')':0, ':':0, ';':0, '-':0, '”':0, '}':0, ']':0, '!':0, '?':0, '/':0}
postPunc = {'(':0, '-':0, '“':0, '{':0, '[':0}


class File(object):
	'''
	A file class containing all references in a file
	'''

	def __init__(self, fname, options):
		'''
		Attributes
		----------
		nom : string
			target file name
		corpus : dictionary of reference list
			 references in the file
		'''
		self.nom = fname
		self.corpus = {}
		self.options = options
	

	def extract(self, typeCorpus, tag, external):
		'''
		Extract references
		
		Parameters
		----------
		typeCorpus : int, {1, 2, 3}
			type of corpus
			1 : corpus 1, 2 : corpus 2...
		tag : string, {"bibl", "note"}
			tag name defining reference types
			"bibl" : corpus 1, "note" : corpus 2
		external : int, {1, 0}
			1 : if the references are external data except CLEO, 0 : if that of CLEO
			it is used to decide whether Bilbo learn call a SVM classification or not.			
		'''	
		clean = Clean()
		if typeCorpus == 1:
			clean = CleanCorpus1()
		elif typeCorpus == 2:
			clean = CleanCorpus2()
			
		references = clean.processing(self.nom, tag, external)
		if len(references) >= 1:
			self.corpus[typeCorpus] = ListReferences(references, typeCorpus)
			rule = Rule()
			rule.reorganizing(self.corpus[typeCorpus])


	def getListReferences(self, typeCorpus):
		'''
		Return reference list
		
		Parameters
		----------
		typeCorpus : int, {1, 2, 3}
			type of corpus
			1 : corpus 1, 2 : corpus 2...
		'''
		try:
			return self.corpus[typeCorpus]
		except :
			return -1
		

	def nbReference(self, typeCorpus):
		'''
		count the number of references
		'''
		try:
			return self.corpus[typeCorpus].nbReference()
			
		except :
			return 0	
			
	
	def _html2unicode(self, tmp_str) :
		#for numerical codes
		matches = re.findall("&#\d+;", tmp_str)
		if len(matches) > 0 :
			hits = set(matches)
			for hit in hits :
				name = hit[2:-1]
				try :
					entnum = int(name)
					tmp_str = tmp_str.replace(hit, unichr(entnum))
				except ValueError:
					pass
	
		#for hex codes
		matches = re.findall("&#[xX][0-9a-fA-F]+;", tmp_str)
		if len(matches) > 0 :
			hits = set(matches)
			for hit in hits :
				hex = hit[3:-1]
				try :
					entnum = int(hex, 16)
					tmp_str = tmp_str.replace(hit, unichr(entnum))
				except ValueError:
					pass
		
		tmp_str = tmp_str.replace('&','&amp;')
		
		return tmp_str

	
	def buildReferences(self, references, tagTypeCorpus, typeCorpus, dirResult):
		'''
		Construct final xml output file, called from Corpus::addTagReferences
		Unlike the first version, compare token by token, replace the token by automatically tagged token. 
		That's why we keep perfectly the original data format
		
		Parameters
		----------
		references : list 
			automatically annotated references by system
		tagTypeCorpus : string, {"bibl", "note"}
			tag name defining reference types
			"bibl" : corpus 1, "note" : corpus 2
				typeCorpus : int, {1, 2, 3}
		type of corpus
			1 : corpus 1, 2 : corpus 2...
		tagTypeList : string, "listbibl"
			tag name wrapping all references
		'''
		cptRef = 0		#reference counter
		tmp_str = ""
		ref_ori = []
		
		'Read the source file to check the initial contents of references'
		for line in open (self.nom, 'r') :
			tmp_str = tmp_str + line
				
		soup = BeautifulSoup (tmp_str)
		s = soup.findAll (tagTypeCorpus)
		
		basicTag = {} #tags existing in the original files
		for ss in s :
			for sss in ss.find_all() :
				basicTag[sss.name] = 1

		tagConvert = {}
		tagConvert = loadTEIRule(tagConvert)
		
		'Reconstruct references by checking input string token by token'
		includedLabels = {}
		for ref in references:
			for reff in ref.find_all() :
				includedLabels[reff.name] = 1
				try : del basicTag[reff.name]
				except : pass 
			parsed_soup = ''.join(s[cptRef].findAll(text = True)) # String only
			ptr = 0
			if (len(parsed_soup.split()) > 0) : #if empty <bibl>, pass it
				oriRef = (str(s[cptRef]))
				for r in ref.contents :
					ck = 0
					try : r.name
					except : ck = 1
					if ck == 0 and not r.name == "c" :
						for token in r.string.split() :
							if token == "&" : token = "&amp;"
							token = token.encode('utf8')
							pre_ptr = ptr
							ptr = oriRef.find(token, ptr)
							inner_string = ""
							if ptr >= 0 :
								tmp_str2 = oriRef[pre_ptr:ptr]
								soup2 = BeautifulSoup (tmp_str2)
								for s2 in soup2 :
									try : inner_string = ''.join(s2.findAll(text = True))
									except : pass
									inner_string = inner_string.encode('utf8')
							#EXCEPTION
							if (ptr < 0) or inner_string.find(token) >= 0 : 
								#try again by eliminating tags
								c = token[0]
								ptr = oriRef.find(c, pre_ptr)
								while (oriRef.find(">", ptr) < oriRef.find("<", ptr)) : # the token is in a tag
									ptr = oriRef.find(c, ptr+1)
								ptr_start = ptr
								newtoken = ""
								if (oriRef.find("</", ptr) < oriRef.find(">", ptr)) : #case) <hi rend="sup">c</hi>Awâd,
									tag_start_l = oriRef.find("<",ptr_start)
									tag_start_r = oriRef.find(">",tag_start_l)
									newtoken = oriRef[ptr_start:tag_start_l]
									mtoken_r = oriRef.find(token[len(token)-1],tag_start_r)
									newtoken += oriRef[tag_start_r+1:mtoken_r+1]
									#print token[len(token)-1], oriRef[mtoken_r+1]
									ptr_start = ptr_start - oriRef[ptr_start:pre_ptr:-1].find("<",0)
									ptr_end = mtoken_r
								else :												#case) B<hi font-variant="small-caps">ayram</hi>
									tag_start_l = oriRef.find("<",ptr_start)
									tag_start_r = oriRef.find(">",tag_start_l)
									tag_end_l = oriRef.find("<",tag_start_r)
									tag_end_r = oriRef.find(">",tag_end_l)
									ptr_end = tag_end_r
									newtoken = oriRef[ptr_start:tag_start_l]+oriRef[tag_start_r+1:tag_end_l]
									newtoken = re.sub(' ', ' ', newtoken)
									newtoken = newtoken.lstrip()
									newtoken = newtoken.rstrip()
								#print ptr, newtoken, token
								if newtoken == token : 
									token = oriRef[ptr_start:ptr_end+1]
									ptr = ptr_start
								else :
									print ptr, newtoken, token
									print "PROBLEM, CANNOT FIND THE TOKEN", token, s[cptRef]
									ptr = -1
									pass
							else :
								while (oriRef.find(">", ptr) < oriRef.find("<", ptr)) : # the token is in a tag
									ptr = oriRef.find(token, ptr+1)
							
							if (ptr >= 0) :
								nstr = "<"+r.name+">"+token+"</"+r.name+">"
								oriRef = oriRef[:ptr] + nstr + oriRef[ptr+len(token):]
								ptr += len(nstr)
								#print oriRef[ptr]
							else :
								ptr = pre_ptr
				
				'check continuously annotated tags to eliminate tags per each token'
				oriRef = self.continuousTags(basicTag, includedLabels, oriRef)
				
				if self.options.o == 'tei' :
					oriRef = toTEI(oriRef, tagConvert)
				ref_ori.append(oriRef)
			cptRef += 1
		
		try:
			cpt = 0
			listRef = soup.findAll(tagTypeCorpus)
			
			p2 = 0
			for ref in listRef:
				contentString ="" # TO CHECK IF THE REFERENCE or NOTE HAS NO CONTENTS
				for rf in ref.contents :
					if rf == rf.string : contentString += rf
						
				for tag in ref.findAll(True) :
						if len(tag.findAll(True)) == 0 and len(tag.contents) > 0 :
							for con in tag.contents :
								contentString += con
				#print contentString, len(contentString.split())
				
				p1 = tmp_str.find('<'+tagTypeCorpus+'>', p2)
				p11 = tmp_str.find('<'+tagTypeCorpus+' ', p2)
				if p1 < 0 or (p11 > 0 and p1 > p11) : p1 = p11
				p2 = tmp_str.find('</'+tagTypeCorpus+'>', p1)
	
				if len(contentString.split()) > 0 :
					doistring = ''
					text = str(ref_ori[cpt])
					if self.options.d :
						doistring = extractDoi(str(references[cpt]), tagTypeCorpus)
						if doistring != '' : 
							text += " <doi>"+str(doistring)+"</doi>"
					tmp_list = list(tmp_str)
					tmp_list[p1:p2+len('</'+tagTypeCorpus+'>')] = text
					tmp_str = ''.join(tmp_list)
				cpt += 1
			
		except :
			pass

		fich = open(dirResult+self._getName(), "w")
		fich.write(tmp_str)
		fich.close()
		
		return

	
	def continuousTags0(self, basicTag, includedLabels, oriRef):
		ptag = ""
		continuousTags = []	#continuously annotated tag array
		noncontinuousck = ["surname", "forename"]
		newsoup = BeautifulSoup(oriRef)
		#print oriRef
		for ns in newsoup.find_all() :
			if ptag == ns.name :
				if ns.name not in noncontinuousck : continuousTags.append(ns.name)
			elif not basicTag.has_key(ns.name) and (len(continuousTags) > 0 and continuousTags[len(continuousTags)-1] != 'NOTAG') :
				continuousTags.append('NOTAG')
			if not basicTag.has_key(ns.name) : ptag = ns.name
			
		ptr = 0
		pretag = ''
		for tmptag in continuousTags :
			if tmptag != 'NOTAG' :
				ptr1 = oriRef.find("</"+tmptag+">", ptr)
				ptr2 = oriRef.find("<"+tmptag+">", ptr1)
				ck = 0
				if oriRef.find(">", ptr1+len("</"+tmptag+">"), ptr2) >= 0 :
					tmpsoup = BeautifulSoup( oriRef[ptr1+len("</"+tmptag+">"):ptr2] )
					#print oriRef[ptr1+len("</"+tmptag+">"):ptr2]
					for ttmp in tmpsoup.find_all() : 
						if ttmp.name in includedLabels : 
							ck = 1
				if ck == 0 :
					token = "</"+tmptag+">"
					oriRef = oriRef[:ptr1] + oriRef[ptr1+len(token):]
					token = "<"+tmptag+">"
					ptr = oriRef.find(token, ptr1)
					
					oriRef = oriRef[:ptr] + oriRef[ptr+len(token):]
				else :
					ptr = ptr2
				pretag = tmptag
			else :
				token = "</"+pretag+">"
				ptr = oriRef.find(token, ptr) + len(token)
				if ptr < 0 : print "PROBLEM OF NONVALID TAGS" #Maybe problem of non-valid tags
	
		return oriRef, continuousTags
	
	
	def wrappedPairs(self, basicTag, includedLabels, oriRef):
		ptr = 0
		newsoup = BeautifulSoup(oriRef)
		for ns in newsoup.find_all() :
			if ns.name in basicTag :
				print ns.name
				ck = 0
				while (ck == 0 and ptr >= 0) :
					ptr = oriRef.find("<"+ns.name, ptr)
					if oriRef[ptr+len("<"+ns.name)] == ' ' or oriRef[ptr+len("<"+ns.name)] == '>' :
						ck = 1
					else : ptr += len("<"+ns.name)
				
				if len(ns.contents) == 1 :
					print oriRef[ptr:ptr+60]
					print ns.name, len(ns.contents), ns.contents, ns.string, 
					try : print ns.contents[0].name
					except : pass
					
		return
	
	
	def continuousTags(self, basicTag, includedLabels, oriRef):
		preTag = ""
		noncontinuousck = ["surname", "forename"]
		newsoup = BeautifulSoup(oriRef)
		ptr2 = 0
		ptr1 = 0
		found = {}
		for ns in newsoup.find_all() :
			if preTag == ns.name and not preTag in noncontinuousck:
				ptr1 = oriRef.find("</"+preTag+">", ptr2)
				ptr2 = oriRef.find("<"+preTag+">", ptr1)
				if oriRef.find(">", ptr1+len("</"+preTag+">"), ptr2) < 0 :
					token = "</"+preTag+">"
					oriRef = oriRef[:ptr1] + oriRef[ptr1+len(token):]
					token = "<"+preTag+">"
					ptr = oriRef.find(token, ptr1)
					oriRef = oriRef[:ptr] + oriRef[ptr+len(token):]
					found[ns.name] = ptr1
				ptr2 = ptr1+1
			else :
				if found.has_key(ns.name) :
					ptr1 = oriRef.find("</"+ns.name+">", ptr2)
					ptr2 = oriRef.find("<"+ns.name+">", ptr1)
			preTag = ns.name
		
		return oriRef

	
	def mismatchedTags(self, oriRef, continuousTags):
		ptr2 = 0
		preTag = ''
		for tmpTag in continuousTags :
			if tmpTag == 'NOTAG' :
				ptr1 = oriRef.find("<"+preTag+">", ptr2)
				ptr2 = oriRef.find("</"+preTag+">", ptr1)
				endck1 = oriRef.find("</", ptr1, ptr2)
				endck2 = oriRef.find(">", endck1, ptr2)
				if endck1 > 0 and endck2 > 0 : #when finding an ending tag in the contents
					ckTag = oriRef[endck1+len("</"):endck2]
					if oriRef.find("<"+ckTag, ptr1, endck1) < 0 :  #when not finding a corresponding starting tag in the contents
						startck1 = (oriRef[ptr1::-1]).find(">", 0)
						startck2 = (oriRef[ptr1::-1]).find("<", startck1)
						if oriRef[ptr1-startck2:ptr1-startck1+1].find("<"+ckTag) == 0 : #find location and exchange tags
							oriRef = oriRef[:ptr1-startck2] + "<"+preTag+">" + oriRef[ptr1-startck2:ptr1-startck1+1] + oriRef[ptr1+len("<"+preTag+">"):]
				ptr1 = ptr1+len("<"+preTag+">")
				ptr2 = oriRef.find("</"+preTag+">", ptr1)
				startck1 = oriRef.rfind("<", ptr1, ptr2)
				startck2 = oriRef.rfind(">", ptr1, ptr2)
				if startck1 >= 0 and startck2 >= 0 and oriRef.rfind("</", startck1, startck2) < 0:  #when finding a starting tag in the contents and no ending tag
					ckTag = ((oriRef[startck1:startck2]).split(">")[0]).split()[0]
					ckTag = ckTag[1:]
					endck1 = oriRef.find("</"+ckTag+">", ptr2+len("</"+preTag+">"))
					endck2 = oriRef.find(">", endck1)
					if oriRef.find("<", ptr2+len("</"+preTag+">"), endck1) < 0 : #find location and exchange tag if there is no other tags in the contents
						oriRef = oriRef[:ptr2] + oriRef[ptr2+len("</"+preTag+">"):endck2+1] + "</"+preTag+">" + oriRef[endck2+1:]	
			preTag = tmpTag
		
		return oriRef
	
	
	def _getName(self):
		'''
		Return the file name without the complete path
		'''
		chemin = self.nom.split("/")
		return chemin.pop()
	

	def convertToUnicode(self, chaine):
		'''
		Convert a string to unicode
		'''
		try:
			if isinstance(chaine, str):
				chaine = unicode(chaine, sys.stdin.encoding)
		except:
			chaine = unicode(chaine, 'ascii')
		return chaine

	