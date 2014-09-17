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
      01/test/test-clean.xml (cleaned for annotation)
 
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
import os
from codecs import open
from formatEval import FormatEval

class Partition():
	# dirName of directory containing the corpus
	# % of test data to fetch from the corpus
	"""
		create "directory-evaluation"
		create "directory-evaluation/10%/" and 01 to 10 folder in it
	"""
	def __init__(self, dirCorpus, testPercentage, numberOfPartition = 10):
		if not os.path.isdir(dirCorpus):
			raise IOError("corpus directory '" + dirCorpus + "' does not exist")
		
		self.createPartitionFolders(dirCorpus, testPercentage, numberOfPartition)
		self.saveAllBibl(dirCorpus)
		self.createEvaluationfiles(dirCorpus, testPercentage, numberOfPartition)
	
	def createPartitionFolders(self, dirCorpus, testPercentage, numberOfPartition = 10):
		dirEval = Partition.getDirEvalName(dirCorpus)
		self.createFolder(dirEval)
		
		dirPercent = Partition.getDirPercentName(dirCorpus, testPercentage)
		self.createFolder(dirPercent)
		
		dirPartitions = Partition.getDirPartitionNames(dirCorpus, testPercentage, numberOfPartition)
		for dirPartition in dirPartitions:
			self.createFolder(dirPartition)
			for testDir in Partition.getDirTestNames(dirPartition):
				self.createFolder(testDir)

	def createEvaluationfiles(self, dirCorpus, testPercentage, numberOfPartition = 10):
		dirPartitions = Partition.getDirPartitionNames(dirCorpus, testPercentage, numberOfPartition)
		for dirPartition in dirPartitions:
			print dirPartition

	def saveAllBibl(self, dirCorpus):
		bibl = FormatEval.getBiblFromDir(dirCorpus)
		biblString = "\n".join(bibl)
		fileName = os.path.join(Partition.getDirEvalName(dirCorpus), 'all_bibl.xml')
		with open(fileName, 'w', encoding='utf-8') as content_file:
			content_file.write(biblString)

	@staticmethod
	def getDirEvalName(dirCorpus):
		return os.path.dirname(dirCorpus) + "-evaluation"

	@staticmethod
	def getDirPercentName(dirCorpus, testPercentage):
		dirEval = Partition.getDirEvalName(dirCorpus)
		return os.path.join(dirEval, str(testPercentage)+'%')

	@staticmethod
	def getDirPartitionNames(dirCorpus, testPercentage, numberOfPartition = 10):
		dirPercent = Partition.getDirPercentName(dirCorpus, testPercentage)
		dirPartitions = []
		for i in range(1, numberOfPartition+1):
			dirPartitions.append(os.path.join(dirPercent, "{:0>2d}" .format(i)))
		return dirPartitions

	@staticmethod
	# given a dirPartition
	# return test, train, model folder
	def getDirTestNames(dirPartition):
		dirEvals = ( os.path.join(dirPartition, testDir) for testDir in ('test', 'train', 'model') )
		return dirEvals
			
		
	def createFolder(sefl, dirName):
		if not os.path.isdir(dirName):
			os.mkdir(dirName)
			print dirName
	




if __name__ == '__main__':
	p = Partition(str(sys.argv[1]), str(sys.argv[2]))
