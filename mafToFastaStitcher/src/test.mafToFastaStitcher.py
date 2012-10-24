##################################################
# Copyright (C) 2012 by 
# Dent Earl (dearl@soe.ucsc.edu, dentearl@gmail.com)
# ... and other members of the Reconstruction Team of David Haussler's 
# lab (BME Dept. UCSC).
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE. 
##################################################
import os
import random
import sys
import unittest
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), '../../include/')))
import mafToolsTest as mtt
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), '../../mafValidator/src/')))
import mafValidator as mafval

g_headers = ['''##maf version=1 scoring=tba.v8
# tba.v8 (((human chimp) baboon) (mouse rat))

''',
             '''##maf version=1 scoring=tba.v8
# tba.v8 (((human chimp) baboon) (mouse rat))
''']
g_knownData = [ ('''a score=0.0 status=test.input
s ref.chr1   10 10 + 100 ACGTACGTAC
s seq1.chr@   0 10 + 100 AAAAAAAAAA
s seq2.chr&  10  5 + 100 -----CCCCC
s seq6.chr1  10  5 + 100 -----GGGGG
s seq7.chr20  0  5 + 100 AAAAA-----

a score=0.0 status=test.input
s ref.chr1   20 10 + 100 GTACGTACGT
s seq1.chra  13  5 + 100 -----AAAAA
s seq2.chr!!  5  5 + 100 CCCCC-----
s seq3.chr0  20  5 + 100 -----GGGGG
s seq6.chr1  22  5 + 100 GGGGG-----

a score=0.0 status=test.input
s ref.chr1   30 10 + 100 ACGTACGTAC
s seq4.chr1   0  5 - 100 GG-----GGG
s seq5.chr2   0 10 + 100 CCCCCCCCCC
s seq7.chr20 42  5 + 100 -----AAAAA
''',
                 ['''> ref.chr1
GGGGGGGGGACGTACGTACGTACGTACGTGGGG
> seq1.chr@
AAAAAAAAAAGG
> seq2.chr&
AAAAAAAAACCCCCAA
> seq2.chr!!
AAAACCCCCAA
> seq3.chr0
AAAAAAAAAAAAAAAAAAAGGGGGAA
> seq4.chr1
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACCCCC
> seq6.chr1
AAAAAAAAAGGGGGAAAAAAAGGGGGAA
> seq7.chr20
AAAAAGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGAAAAATT
'''],
                 '''> ref.chr1
ACGTACGTAC-----------------GTACGTACGT-------------
------------------------ACGTACGTAC
> seq1
AAAAAAAAAA----------------------AAAAA-------------
----------------------------------
> seq2
-----CCCCC------------NNNNNCCCCC------------------
----------------------------------
> seq6.chr1
-----GGGGGAAAAAAAGGGGG----------------------------
----------------------------------
> seq7.chr20
AAAAA--------------------------------GGGGGGGGGGGGG
GGGGGGGGGGGGGGGGGGGGGGGG-----AAAAA
> seq3.chr0
--------------------------------GGGGG-------------
----------------------------------
> seq4.crh1
--------------------------------------------------
------------------------GG-----GGG
> seq5.chr2
--------------------------------------------------
------------------------CCCCCCCCCC
''',
                 '''a stitched=true
s ref.chr1 10 30 + 100 ACGTACGTAC------------------------------GTACGTACGT-------------------------------------ACGTACGTAC
s seq1      0 15 +  15 AAAAAAAAAANNNNNN-----------------------------AAAAA-----------------------------------------------
s seq2      0 15 +  15 -----CCCCC------NNNNNN------------------CCCCC----------------------------------------------------
s seq6      0 17 +  17 -----GGGGG-----------------AAAAAAA------GGGGG----------------------------------------------------
s seq7      0 47 +  47 AAAAA-----------------------------NNNNNN-----AAAAA-----------------------------------------------
s seq3      0  5 +   5 ---------------------------------------------GGGGG-----------------------------------------------
s seq4      0  5 -   5 ---------------------------------------------------------------------------------------GG-----GGG
s seq5      0 10 +  10 ---------------------------------------------------------------------------------------CCCCCCCCCC
''',
                 ),
                ]

def hashify(s):
    if s is None:
        return None
    return s.replace(' ', '').replace('\n', '')
def fastaIsCorrect(filename, expected):
    f = open(filename)
    obs = ''
    for line in f:
        obs += line
    if hashify(obs) != hashify(expected):
        print '\ndang'
        print 'observed:'
        print obs
        print '!='
        print 'expected:'
        print expected
        return False
    return True
def mafIsCorrect(filename, expected):
    f = open(filename)
    lastLine = mtt.processHeader(f)
    # walk through the maf, assessing the equivalence to the blockList items
    b = mtt.extractBlockStr(f, lastLine)
    maf = ''
    while (b is not None):
        lastLine = None
        maf += b
        b = mtt.extractBlockStr(f, lastLine)
    if hashify(maf) != hashify(expected):
        print '\ndang'
        print 'observed:'
        print maf
        print '!='
        print 'expected:'
        print expected
        return False
    return True
def testFasta(path, fastaList):
    i = 0
    names = []
    for fasta in fastaList:
        fasta = fasta.split('\n')
        name = os.path.join(path, 'fasta_%d.fa' % i)
        names.append(name)
        f = open(name, "w")
        for line in fasta:
            f.write('%s\n' % line)
        f.close()
        i += 1
    return ','.join(names)
class CuTest(unittest.TestCase):
    def testAllTests(self):
        """ If valgrind is installed on the system, check for memory related errors in CuTests
        """
        mtt.makeTempDirParent()
        valgrind = mtt.which('valgrind')
        if valgrind is None:
            return
        tmpDir = os.path.abspath(mtt.makeTempDir('memory0'))
        customOpts = mafval.GenericValidationOptions()
        parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cmd = mtt.genericValgrind(tmpDir)
        cmd.append(os.path.abspath(os.path.join(parent, 'test', 'allTests')))
        outpipes = [os.path.join('/dev', 'null')]
        mtt.recordCommands([cmd], tmpDir)
        mtt.runCommandsS([cmd], tmpDir, outPipes=outpipes)
        self.assertTrue(mtt.noMemoryErrors(os.path.join(tmpDir, 'valgrind.xml')))
        mtt.removeDir(tmpDir)
class FastaStitchTest(unittest.TestCase):
    def testFastaStitch(self):
        """ mafToFastaStitcher should produce known output for a given known input
        """
        mtt.makeTempDirParent()
        tmpDir = os.path.abspath(mtt.makeTempDir('fasta'))
        customOpts = mafval.GenericValidationOptions()
        for inMaf, inFaList, outFa, outMaf  in g_knownData:
            testMaf = mtt.testFile(os.path.abspath(os.path.join(tmpDir, 'test.maf')),
                                   ''.join(inMaf), g_headers)
            testFaNames = testFasta(os.path.abspath(tmpDir), inFaList)
            parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            cmd = [os.path.abspath(os.path.join(parent, 'test', 'mafToFastaStitcher')), 
                   '--maf', os.path.abspath(os.path.join(tmpDir, 'test.maf')),
                   '--seqs', testFaNames,
                   '--breakpointPenalty', '6', '--interstitialSequence', '20',
                   '--outMfa', os.path.abspath(os.path.join(tmpDir, 'out.fa'))]
            mtt.recordCommands([cmd], tmpDir)
            mtt.runCommandsS([cmd], tmpDir)
            self.assertTrue(fastaIsCorrect(os.path.abspath(os.path.join(tmpDir, 'out.fa')), outFa))
            # self.assertTrue(fastaIsCorrect(os.path.abspath(os.path.join(tmpDir, 'out.maf')), outMaf))
            # self.assertTrue(mafval.validateMaf(os.path.join(tmpDir, 'out.maf'), customOpts))
        mtt.removeDir(tmpDir)
    def dtestMemory1(self):
        """ If valgrind is installed on the system, check for memory related errors (1).
        """
        mtt.makeTempDirParent()
        valgrind = mtt.which('valgrind')
        if valgrind is None:
            return
        tmpDir = os.path.abspath(mtt.makeTempDir('memory1'))
        customOpts = mafval.GenericValidationOptions()
        for a, expected, strand in g_blocks:
            testMaf = mtt.testFile(os.path.abspath(os.path.join(tmpDir, 'test.maf')),
                                   ''.join(a), g_headers)
            parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            cmd = mtt.genericValgrind(tmpDir)
            cmd += [os.path.abspath(os.path.join(parent, 'test', 'mafStrander')), 
                    '--maf', os.path.abspath(os.path.join(tmpDir, 'test.maf')),
                    '--seq', 'target', '--strand', strand]
            outpipes = [os.path.abspath(os.path.join(tmpDir, 'coerced.maf'))]
            mtt.recordCommands([cmd], tmpDir, outPipes=outpipes)
            mtt.runCommandsS([cmd], tmpDir, outPipes=outpipes)
            self.assertTrue(mtt.noMemoryErrors(os.path.join(tmpDir, 'valgrind.xml')))
            self.assertTrue(mafval.validateMaf(os.path.join(tmpDir, 'coerced.maf'), customOpts))
        mtt.removeDir(tmpDir)

if __name__ == '__main__':
    unittest.main()
