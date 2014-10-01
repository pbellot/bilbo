# -*- coding: utf-8 -*-
from __future__ import unicode_literals
"""
 Given a directory with annotated xml file and a percentage of test data
 create "directory-evaluation"
 create all_bibl.xml file in "directory-evaluation"
 count number of bibl
 create "directory-evaluation/10%/" and 01 to 10 folder in it
  in each folder create
    3 folders :
      01/test/
      01/train/
      01/model/
    3 files :
      01/test.xml with 10% bibl (random) (labeled for evaluation)
      01/train/train.xml with 90% of remaining bibl
      01/test/test_clean.xml (cleaned for annotation)
 
 foreach directory-evaluation/10%/ directory
   train bilbo with 01/train/train.xml file
   save model in 01/model/
 
 foreach directory-evaluation/10%/ directory
   label with bilbo 01/test/test-clean.xml and 01/model/
   do evaluation with 01/test.xml and 01/result/testEstCRF.xml
   save result in 01/evalution.txt
     append macro-precision result in 10%/evaluation.csv
"""

'''
Create a list of <bibl> from a file
Get a list and split it in x randomly
create folder
launch bilbo
'''

import sys
if __name__ == '__main__':
	sys.path.append('src/')
import os
from codecs import open
from bilbo.Bilbo import Bilbo
from formatEval import FormatEval

class Partition():
	# dirName of directory containing the corpus
	# % of test data to fetch from the corpus
	"""
		create "directory-evaluation"
		create "directory-evaluation/10%/" and 01 to 10 folder in it
	"""
	def __init__(self, dirCorpus, testPercentage, numberOfPartition=10, prefix=''):
		if not os.path.isdir(dirCorpus):
			raise IOError("corpus directory '" + dirCorpus + "' does not exist")
		self.dirCorpus = dirCorpus
		self.prefix = "-eval" + ("-" + prefix if prefix else "")
		self.testPercentage = testPercentage
		self.numberOfPartition = int(numberOfPartition)

	def partition(self):
		self.createPartitionFolders(self.dirCorpus, self.testPercentage, self.numberOfPartition)
		allBibl = self.getAndSaveAllBibl(self.dirCorpus)
		self.createEvaluationfiles(self.dirCorpus, self.testPercentage, self.numberOfPartition, allBibl)
		

	def createPartitionFolders(self, dirCorpus, testPercentage, numberOfPartition = 10):
		dirEval = self.getDirEvalName()
		self.createFolder(dirEval)
		
		dirPercent = self.getDirPercentName()
		self.createFolder(dirPercent)
		
		dirPartitions = self.getDirPartitionNames()
		for dirPartition in dirPartitions:
			self.createFolder(dirPartition)
			for testDir in self.getDirTestNames(dirPartition):
				self.createFolder(testDir)

	def createEvaluationfiles(self, dirCorpus, testPercentage, numberOfPartition, allBibl):
		dirPartitions = self.getDirPartitionNames()
		for dirPartition in dirPartitions:
			(annotateDir, testDir, trainDir, modelDir, _) = self.getDirTestNames(dirPartition)
			testCorpus, trainCorpus = FormatEval.getShuffledCorpus(allBibl, testPercentage)
			
			trainFile = os.path.join(trainDir, 'train.xml')
			self.saveListToFile(trainCorpus, trainFile)
			
			cleanCorpus = FormatEval.stripTags(testCorpus)
			cleanFile = os.path.join(annotateDir, 'test_clean.xml')
			self.saveListToFile(cleanCorpus, cleanFile)

			# In test.xml we need to duplicate <bibl> inside <bibl>, in order to present the same data for evaluation
			# Bilbo does not format the "same" data equaly between train and annotation
			evalFile = os.path.join(testDir, 'test.xml')
			testCorpus = FormatEval.getBiblList("\n".join(testCorpus))
			self.saveListToFile(testCorpus, evalFile)
			#print evalFile, trainFile, cleanFile
			#print testCorpus, trainCorpus, cleanCorpus

	def getAndSaveAllBibl(self, dirCorpus):
		allBibl = FormatEval.getBiblFromDir(dirCorpus)
		fileName = os.path.join(self.getDirEvalName(), 'all_bibl.xml')
		self.saveListToFile(allBibl, fileName)
		return allBibl

	def getDirEvalName(self):
		return os.path.dirname(self.dirCorpus + os.sep) + self.prefix

	def getDirPercentName(self):
		dirEval = self.getDirEvalName()
		return os.path.join(dirEval, str(self.testPercentage)+'%')

	def getDirPartitionNames(self):
		dirPercent = self.getDirPercentName()
		dirPartitions = []
		for i in range(1, self.numberOfPartition+1):
			dirPartitions.append(os.path.join(dirPercent, "{:0>2d}" .format(i)))
		return dirPartitions

	# return annotate, test, train, model folder
	def getDirTestNames(self, dirPartition):
		dirEvals = ( os.path.join(dirPartition, testDir) for testDir in ('annotate', 'test', 'train', 'model/', 'result') )
		return dirEvals

	def saveListToFile(self, myList, fileName):
		myString = "<listBibl>\n" + "\n".join(myList) + "\n</listBibl>\n"
		if type(myString) is str:
			print "String not unicode ! It shouldn't."
		with open(fileName, 'w', encoding='utf-8') as content_file:
			content_file.write(myString)

	def createFolder(self, dirName):
		if not os.path.isdir(dirName):
			os.mkdir(dirName)
			#print dirName



if __name__ == '__main__':
	# usage python src/bilbo/evalution/partition.py dirCorpus 10
	numberOfPartition = int(sys.argv[3]) if len(sys.argv)>=4 else 10
	prefix = sys.argv[4] if len(sys.argv)>=5 else ''
	p = Partition(str(sys.argv[1]), str(sys.argv[2]), numberOfPartition, prefix)
	p.partition()