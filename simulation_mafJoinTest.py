"""Test for mafJoin

"""

import os, sys, subprocess, re
myBinDir = os.path.normpath(os.path.dirname(sys.argv[0]))
sys.path.append(myBinDir + "/../..")
os.environ["PATH"] = myBinDir + "/../../../bin:" + os.environ["PATH"]

import unittest
from sonLib.bioio import getTempFile 
from sonLib.bioio import logger
from sonLib.bioio import system

class MafJoinTests(unittest.TestCase):

    def getTestTempFile(self, suffix):
        # FIXME: make this part of test framework
        tempDir = "tmp"
        if not os.path.exists(tempDir):
            os.makedirs(tempDir)
        tempFile = tempDir + "/" + self.id() + "." + suffix
        if os.path.exists(tempFile):
            os.unlink(tempFile)
        return tempFile
    
    def writeMAF(self, maf, suffix):
        """Takes one of the above MAF strings and writes it to temp file.
        """
        tempFile = self.getTestTempFile(suffix)
        fileHandle = open(tempFile, 'w')
        fileHandle.write("##maf version=1\n")
        # skip first blank line
        for line in maf.split("\n")[1:]:
            fileHandle.write(line.strip() + "\n")
        fileHandle.close()
        return tempFile

    def makeMafJoinCmd(self, refDb, mafFileA, mafFileB, outputMafFile, treelessRoot1=None, treelessRoot2=None, maxBlkWidth=None):
        cmd = ["mafJoin"]
        if treelessRoot1 != None:
            cmd.append("-treelessRoot1="+treelessRoot1)
        if treelessRoot2 != None:
            cmd.append("-treelessRoot2="+treelessRoot2)
        if maxBlkWidth != None:
            cmd.append("-maxBlkWidth="+str(maxBlkWidth))
        cmd.extend([refDb, mafFileA, mafFileB, outputMafFile])
        return cmd

    def __stdFlush(self):
        sys.stdout.flush()
        sys.stderr.flush()

    def runMafJoin(self, refDb, mafFileA, mafFileB, outputMafFile, expectExitCode=0, expectStderr=None, expectStderrRe=None, treelessRoot1=None, treelessRoot2=None, maxBlkWidth=None):
        self.__stdFlush()
        cmd = self.makeMafJoinCmd(refDb, mafFileA, mafFileB, outputMafFile, treelessRoot1, treelessRoot2, maxBlkWidth)
        logger.info("run: " + " ".join(cmd))
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (stdout, stderr) = proc.communicate()
        exitCode = proc.wait()
        self.assertEquals(exitCode, expectExitCode)
        self.assertEquals(stdout, "")
        if expectStderr != None:
            self.assertEquals(stderr, expectStderr)
        elif expectStderrRe != None:
            if re.search(expectStderrRe, stderr) == None:
                self.assertEquals(stderr, expectStderrRe)
        else:
            if stderr != "":
                sys.stderr.write(stderr)
                self.__stdFlush()
            self.assertEquals(stderr, "")
        logger.info("okay: " + " ".join(cmd))

    def compareExpectedAndRecieved(self, expected, recieved):
        """Checks two MAFs are equivalent.
        """
        system("diff -u %s %s" % (expected, recieved))

    def mafJoinTest(self, ref, mafA, mafB, mafC, expectExitCode=0, expectStderr=None, expectStderrRe=None, treelessRoot1=None, treelessRoot2=None, maxBlkWidth=None):
        """Writes out mafA and mafB to temp files.
        Runs mafJoin
        Parses the output and compares it to mafC.
        """
        tempFileA = self.writeMAF(mafA, "A.maf")
        tempFileB = self.writeMAF(mafB, "B.maf")
        tempFileC = self.writeMAF(mafC, "C.maf")
        tempOutputFile = self.getTestTempFile("out.maf")
        self.runMafJoin(ref, tempFileA, tempFileB, tempOutputFile, expectExitCode=expectExitCode, expectStderr=expectStderr, expectStderrRe=expectStderrRe, treelessRoot1=treelessRoot1, treelessRoot2=treelessRoot2, maxBlkWidth=maxBlkWidth)
        if expectExitCode == 0:  # only check MAF on success
            self.compareExpectedAndRecieved(tempFileC, tempOutputFile)

    def setUp(self):
        unittest.TestCase.setUp(self)
    
    def tearDown(self):
        unittest.TestCase.tearDown(self)
        
    def testJoin1(self):
        """Simple non-dup join. Shows splitting of blocks.
        Note the join process should maintain the ordering of rows in columns.
        """
        A = """
        a score=50.0 tree=\"(hg18.chr7:0.1,mm4.chr6:0.15)rn3.chr4;\"
        s hg18.chr7    27578828 38 + 158545518 AAA-GGGAATGTTAACCAAATGA---ATTGTCTCTTACGGTG
        s mm4.chr6     53215344 38 + 151104725 -AATGGGAATGTTAAGCAAACGA---ATTGTCTCTCAGTGTG
        s rn3.chr4     81344243 40 + 187371129 -AA-GGGGATGCTAAGCCAATGAGTTGTTGTCTCTCAATGTG
        """
        B = """
        a score=5.0 tree=\"(panTro1.chr6:0.3,baboon.chr6:0.2)hg18.chr7;\"
        s panTro1.chr6 28741140 33 + 161576975 AAAGGGAATGTTAACCAAATGAATTGTCTCTTA
        s baboon.chr6    116834 33 +   4622798 AAAGGGAATGTTAACCAAATGAGTTGTCTCTTA
        s hg18.chr7    27578828 33 + 158545518 AAAGGGAATGTTAACCAAATGAATTGTCTCTTA
        """
        C = """
        a score=0.000000 tree="((baboon.chr6:0.2,panTro1.chr6:0.3)hg18.chr7:0.1,mm4.chr6:0.15)rn3.chr4;"
        s baboon.chr6    116834 33 +   4622798 AAA-GGGAATGTTAACCAAATGA---GTTGTCTCTTA-----
        s panTro1.chr6 28741140 33 + 161576975 AAA-GGGAATGTTAACCAAATGA---ATTGTCTCTTA-----
        s hg18.chr7    27578828 38 + 158545518 AAA-GGGAATGTTAACCAAATGA---ATTGTCTCTTACGGTG
        s mm4.chr6     53215344 38 + 151104725 -AATGGGAATGTTAAGCAAACGA---ATTGTCTCTCAGTGTG
        s rn3.chr4     81344243 40 + 187371129 -AA-GGGGATGCTAAGCCAATGAGTTGTTGTCTCTCAATGTG
        """
        self.mafJoinTest("hg18", A, B, C)
    
    def testJoin2(self):
        """Simple non-dup join. Shows ordering of inserts, first from A then from B.
        """
        A = """
        a score=10.0 tree=\"(hg18.chr7:0.1,mm4.chr6:0.15)rn3.chr4;\"
        s hg18.chr7    27699739 3 + 158545518 T---GA
        s mm4.chr6     53303881 6 + 151104725 TAAAGA
        s rn3.chr4     81444246 6 + 187371129 taagga
        """
        B = """
        a score=1000.0 tree=\"(panTro1.chr6:0.3,baboon.chr6:0.2)hg18.chr7;\"
        s panTro1.chr6 28862317 6 + 161576975 TAAAGA
        s baboon.chr6    241163 3 +   4622798 T---GA
        s hg18.chr7    27699739 3 + 158545518 T---GA
        """
        C = """
        a score=0.000000 tree="((baboon.chr6:0.2,panTro1.chr6:0.3)hg18.chr7:0.1,mm4.chr6:0.15)rn3.chr4;"
        s baboon.chr6    241163 3 +   4622798 T------GA
        s panTro1.chr6 28862317 6 + 161576975 T---AAAGA
        s hg18.chr7    27699739 3 + 158545518 T------GA
        s mm4.chr6     53303881 6 + 151104725 TAAA---GA
        s rn3.chr4     81444246 6 + 187371129 taag---ga
        """
        self.mafJoinTest("hg18", A, B, C)
    
    def testJoin3(self):
        """Simple non-dup join. Shows merging of blocks. Shows merging of trees at a 
        birfurcation.
        """
        A = """
        a score=5.0 tree=\"(mm4.chr6:0.15)hg18.chr7;\"
        s mm4.chr6     53310102 2 - 151104725 AC
        s hg18.chr7    27707221 2 + 158545518 gc
        
        a score=5.0 tree=\"(mm4.chr6:0.15)hg18.chr7;\"
        s mm4.chr6     53310104 11 - 151104725 AGCTGAAAATA
        s hg18.chr7    27707223 11 + 158545518 agctgaaaaca
        """
        B = """
        a score=2.0 tree=\"((panTro1.chr6:0.3)baboon.chr6:0.2)hg18.chr7;\"
        s panTro1.chr6 28869787 5 + 161576975 gcagc-
        s baboon.chr6    249182 5 -   4622798 gcagc-
        s hg18.chr7    27707221 6 + 158545518 gcagct
        
        a score=2.0 tree=\"((panTro1.chr6:0.3)baboon.chr6:0.2)hg18.chr7;\"
        s panTro1.chr6 28869792 7 + 161576975 gaaaaca
        s baboon.chr6    249187 7 -   4622798 gaaaaca
        s hg18.chr7    27707227 7 + 158545518 gaaaaca
        """ 
        C = """
        a score=0.000000 tree="((panTro1.chr6:0.3)baboon.chr6:0.2,mm4.chr6:0.15)hg18.chr7;"
        s panTro1.chr6 28869787 12 + 161576975 gcagc-gaaaaca
        s baboon.chr6    249182 12 -   4622798 gcagc-gaaaaca
        s mm4.chr6     53310102 13 - 151104725 ACAGCTGAAAATA
        s hg18.chr7    27707221 13 + 158545518 gcagctgaaaaca
        """
        self.mafJoinTest("hg18", A, B, C)

    def testJoin4(self):
        """Dup join. Contains dups of non-ref sequences and simple split
        """
        A = """
        a score=5.0 tree=\"((baboon.chr6:0.3,baboon.chr6:0.1)panTro1.chr6:0.2)hg18.chr7;\"
        s baboon.chr6    116834 37 +   4622798 AAAGGGAATGTTAACCAAATGAGTTGTCTCTTATGGT
        s baboon.chr6    126834 37 +   4622798 AAAGGGAATGTTAACCAAATGAGTTGTCTCTTATGGT
        s panTro1.chr6 28741140 37 + 161576975 AAAGGGAATGTTAACCAAATGAATTGTCTCTTACGGT
        s hg18.chr7    27578828 37 + 158545518 AAAGGGAATGTTAACCAAATGAATTGTCTCTTACGGT
        """
        B = """
        a score=50.0 tree=\"((mm4.chr6:0.15,mm4.chr7:0.14)rn3.chr4:0.15,rn3.chr4:0.14)hg18.chr7;\"
        s mm4.chr6     53215344 38 + 151104725 -AATGGGAATGTTAAGCAAACGA---ATTGTCTCTCAGTGTG
        s mm4.chr7     50000000 40 + 150000000 AAATGGGAATGTTAAGCAAACGAT--ATTGTCTCTCAGTGTG
        s rn3.chr4     81344243 40 + 187371129 -AA-GGGGATGCTAAGCCAATGAGTTGTTGTCTCTCAATGTG
        s rn3.chr4     80000000 35 - 187371129 -AA-GGGGATG-----CCAATGAGTTGTTGTCTCTCAATGTG
        s hg18.chr7    27578828 38 + 158545518 AAA-GGGAATGTTAACCAAATGA---ATTGTCTCTTACGGTG
        """
        C = """
        a score=0.000000 tree="((baboon.chr6:0.3,baboon.chr6:0.1)panTro1.chr6:0.2,(mm4.chr6:0.15,mm4.chr7:0.14)rn3.chr4:0.15,rn3.chr4:0.14)hg18.chr7;"
        s baboon.chr6    116834 37 +   4622798 AAA-GGGAATGTTAACCAAATGA---GTTGTCTCTTATGGT-
        s baboon.chr6    126834 37 +   4622798 AAA-GGGAATGTTAACCAAATGA---GTTGTCTCTTATGGT-
        s panTro1.chr6 28741140 37 + 161576975 AAA-GGGAATGTTAACCAAATGA---ATTGTCTCTTACGGT-
        s mm4.chr6     53215344 38 + 151104725 -AATGGGAATGTTAAGCAAACGA---ATTGTCTCTCAGTGTG
        s mm4.chr7     50000000 40 + 150000000 AAATGGGAATGTTAAGCAAACGAT--ATTGTCTCTCAGTGTG
        s rn3.chr4     81344243 40 + 187371129 -AA-GGGGATGCTAAGCCAATGAGTTGTTGTCTCTCAATGTG
        s rn3.chr4     80000000 35 - 187371129 -AA-GGGGATG-----CCAATGAGTTGTTGTCTCTCAATGTG
        s hg18.chr7    27578828 38 + 158545518 AAA-GGGAATGTTAACCAAATGA---ATTGTCTCTTACGGTG
        """
        self.mafJoinTest("hg18", A, B, C)
        
    def testJoin5(self):
        """Dup join contains dups of both ref and non-ref sequences.
        Note the dupped ref human sequences maintain there position in the
        final maf. Once again, the join process should maintain the ordering of sequences in columns.
        This case is interesting as it contains an inserted human base in the dup - I'm allowing
        this, but you might want to consider it illegal and change the test. 
        """
        A = """
        a score=1000.0 tree=\"((panTro1.chr6:0.3,panTro1.chr6:0.1)baboon.chr6:0.2)hg18.chr7;\"
        s panTro1.chr6 28862317 6 + 161576975 TAAAGA
        s panTro1.chr6 29862317 6 + 161576975 TAAAGA
        s baboon.chr6    241163 3 +   4622798 T---GA
        s hg18.chr7    27699739 3 + 158545518 T---GA
        """
        B = """
        a score=10.0 tree=\"((hg18.chr7:0.1,hg18.chr7:0.5)mm4.chr6:0.15)rn3.chr4;\"
        s hg18.chr7    27699739 3 + 158545518 T---GA
        s hg18.chr7    27000000 5 + 158545518 T-GGGA
        s mm4.chr6     53303881 6 + 151104725 TAAAGA
        s rn3.chr4     81444246 6 + 187371129 taagga
        """
        C = """
        a score=0.000000 tree="((hg18.chr7:0.5,((panTro1.chr6:0.3,panTro1.chr6:0.1)baboon.chr6:0.2)hg18.chr7:0.1)mm4.chr6:0.15)rn3.chr4;"
        s hg18.chr7    27000000 5 + 158545518 T----GGGA
        s panTro1.chr6 28862317 6 + 161576975 TAAA---GA
        s panTro1.chr6 29862317 6 + 161576975 TAAA---GA
        s baboon.chr6    241163 3 +   4622798 T------GA
        s hg18.chr7    27699739 3 + 158545518 T------GA
        s mm4.chr6     53303881 6 + 151104725 T---AAAGA
        s rn3.chr4     81444246 6 + 187371129 t---aagga
        """
        self.mafJoinTest("hg18", A, B, C)
        
    def testJoin6(self):
        """Dup multiple in the reference which joins to sequences..
        """
        A = """
        a score=2.0 tree=\"((hg18.chr7:0.1,hg18.chr9:0.5)panTro1.chr6:0.15)baboon.chr6;\"
        s hg18.chr7    27707221 13 + 158545518 gcagctgaaaaca
        s hg18.chr9    27707221 13 + 158545518 gcagctgaaaaca
        s panTro1.chr6 28869787 13 + 161576975 gcagctgaaaaca
        s baboon.chr6    249182 13 -   4622798 gcagctgaaaaca
        """
        B = """
        a score=5.0 tree=\"(mm4.chr6:0.1)hg18.chr7;\"
        s mm4.chr6     53310102 13 - 151104725 ACAGCTGAAAATA
        s hg18.chr7    27707221 13 + 158545518 gcagctgaaaaca
        
        a score=5.0 tree=\"(mm4.chr6:0.2)hg18.chr9;\"
        s mm4.chr6     54310102 13 - 151104725 ACAGCTGAAAATA
        s hg18.chr9    27707221 13 + 158545518 gcagctgaaaaca
        """
        C = """
        a score=0.000000 tree=\"(((mm4.chr6:0.1)hg18.chr7:0.1,(mm4.chr6:0.2)hg18.chr9:0.5)panTro1.chr6:0.15)baboon.chr6;\"
        s mm4.chr6     53310102 13 - 151104725 ACAGCTGAAAATA
        s hg18.chr7    27707221 13 + 158545518 gcagctgaaaaca
        s mm4.chr6     54310102 13 - 151104725 ACAGCTGAAAATA
        s hg18.chr9    27707221 13 + 158545518 gcagctgaaaaca
        s panTro1.chr6 28869787 13 + 161576975 gcagctgaaaaca
        s baboon.chr6    249182 13 -   4622798 gcagctgaaaaca
        """
        self.mafJoinTest("hg18", A, B, C)
          
    def testJoin7(self):
        """MAFs with no trees
        """
        A = """
        a score=2.0
        s hg18.chr7    27707221 13 + 158545518 gcagctgaaaaca
        s baboon.chr6    249182 13 -   4622798 gcagctgaaaaca
        """
        B = """
        a score=5.0
        s hg18.chr7    27707221 13 + 158545518 gcagctgaaaaca
        s mm4.chr6     53310102 13 - 151104725 ACAGCTGAAAATA
        """
        C = """
        a score=0.000000 tree="(baboon.chr6:0.1,mm4.chr6:0.1)hg18.chr7;"
        s baboon.chr6   249182 13 -   4622798 gcagctgaaaaca
        s mm4.chr6    53310102 13 - 151104725 ACAGCTGAAAATA
        s hg18.chr7   27707221 13 + 158545518 gcagctgaaaaca
        """
        self.mafJoinTest("hg18", A, B, C, treelessRoot1="hg18", treelessRoot2="hg18")
          
    def testJoin8(self):
        """simple duplication represented by two separate blocks, as with evolver
        """
        A = """
        a score=10.0 tree=\"(hg18.chr7:0.1,mm4.chr6:0.15)rn3.chr4;\"
        s hg18.chr7    27699739 3 + 158545518 T---GA
        s mm4.chr6     53303881 6 + 151104725 TAAAGA
        s rn3.chr4     81444246 6 + 187371129 taagga

        a score=10.0 tree=\"(mm4.chr6:0.15)rn3.chr4;\"
        s mm4.chr6     54303881 6 + 151104725 TAAAGA
        s rn3.chr4     81444246 6 + 187371129 taagga
        """
        B = """
        a score=1000.0 tree=\"(panTro1.chr6:0.3,baboon.chr6:0.2)hg18.chr7;\"
        s panTro1.chr6 28862317 6 + 161576975 TAAAGA
        s baboon.chr6    241163 3 +   4622798 T---GA
        s hg18.chr7    27699739 3 + 158545518 T---GA
        """
        C = """
        a score=0.000000 tree="((baboon.chr6:0.2,panTro1.chr6:0.3)hg18.chr7:0.1,mm4.chr6:0.15,mm4.chr6:0.15)rn3.chr4;"
        s baboon.chr6    241163 3 +   4622798 T------GA
        s panTro1.chr6 28862317 6 + 161576975 T---AAAGA
        s hg18.chr7    27699739 3 + 158545518 T------GA
        s mm4.chr6     53303881 6 + 151104725 TAAA---GA
        s mm4.chr6     54303881 6 + 151104725 TAAA---GA
        s rn3.chr4     81444246 6 + 187371129 taag---ga
        """
        self.mafJoinTest("hg18", A, B, C)
    
    def testJoin9(self):
        """multiple duplications that don't have exact same bounds and include
        a reverse complement.
        """
        A = """
        a score=10.0 tree=\"(hg18.chr7:0.1,mm4.chr6:0.15)rn3.chr4;\"
        s hg18.chr7    27699739 3 + 158545518 T---GA
        s mm4.chr6     53303881 6 + 151104725 TAAAGA
        s rn3.chr4     81444246 6 + 187371129 taagga

        a score=10.0 tree=\"(mm4.chr6:0.15)rn3.chr4;\"
        s mm4.chr6     54303882 5 + 151104725 AAAG-A
        s rn3.chr4     81444247 6 + 187371129 aaggaa

        a score=10.0 tree=\"(mm4.chr8:0.15)rn3.chr4;\"
        s mm4.chr8     54303880 11 + 151104725 CATTCCTTAAC
        s rn3.chr4     105926875 9 - 187371129 c-ttcctta-c
        """
        B = """
        a score=1000.0 tree=\"(panTro1.chr6:0.3,baboon.chr6:0.2)hg18.chr7;\"
        s panTro1.chr6 28862317 6 + 161576975 TAAAGA
        s baboon.chr6    241163 3 +   4622798 T---GA
        s hg18.chr7    27699739 3 + 158545518 T---GA
        """
        C = """
        a score=0.000000 tree="((baboon.chr6:0.2,panTro1.chr6:0.3)hg18.chr7:0.1,mm4.chr6:0.15,mm4.chr6:0.15,mm4.chr8:0.15)rn3.chr4;"
        s baboon.chr6    241163  3 +   4622798 --T------GA---
        s panTro1.chr6 28862317  6 + 161576975 --T---AAAGA---
        s hg18.chr7    27699739  3 + 158545518 --T------GA---
        s mm4.chr6     53303881  6 + 151104725 --TAAA---GA---
        s mm4.chr6     54303882  5 + 151104725 ---AAA---G-A--
        s mm4.chr8     96800834 11 - 151104725 GTTAAG---GAATG
        s rn3.chr4     81444245  9 + 187371129 g-taag---gaa-g
        """
        self.mafJoinTest("hg18", A, B, C)

    def testJoin10(self):
        """regression where second block got lost
        """
        # this was a buggy version of testJoin9
        A = """
        a score=10.0 tree=\"(hg18.chr7:0.1,mm4.chr6:0.15)rn3.chr4;\"
        s hg18.chr7    27699739 3 + 158545518 T---GA
        s mm4.chr6     53303881 6 + 151104725 TAAAGA
        s rn3.chr4     81444246 6 + 187371129 taagga

        a score=10.0 tree=\"(mm4.chr6:0.15)rn3.chr4;\"
        s mm4.chr6     54303882 5 + 151104725 AAAG-A
        s rn3.chr4     81444247 6 + 187371129 aaggaa

        a score=10.0 tree=\"(mm4.chr8:0.15)rn3.chr4;\"
        s mm4.chr8     54303880 11 + 151104725 CATTCCTTAAC
        s rn3.chr4     105926875 9 + 187371129 c-ttcctta-c
        """
        B = """
        a score=1000.0 tree=\"(panTro1.chr6:0.3,baboon.chr6:0.2)hg18.chr7;\"
        s panTro1.chr6 28862317 6 + 161576975 TAAAGA
        s baboon.chr6    241163 3 +   4622798 T---GA
        s hg18.chr7    27699739 3 + 158545518 T---GA
        """
        C = """
        a score=0.000000 tree="((baboon.chr6:0.2,panTro1.chr6:0.3)hg18.chr7:0.1,mm4.chr6:0.15,mm4.chr6:0.15)rn3.chr4;"
        s baboon.chr6    241163 3 +   4622798 T------GA-
        s panTro1.chr6 28862317 6 + 161576975 T---AAAGA-
        s hg18.chr7    27699739 3 + 158545518 T------GA-
        s mm4.chr6     53303881 6 + 151104725 TAAA---GA-
        s mm4.chr6     54303882 5 + 151104725 -AAA---G-A
        s rn3.chr4     81444246 7 + 187371129 taag---gaa

        a score=0.000000 tree="(mm4.chr8:0.15)rn3.chr4;"
        s mm4.chr8  54303880 11 + 151104725 CATTCCTTAAC
        s rn3.chr4 105926875  9 + 187371129 c-ttcctta-c
        """
        self.mafJoinTest("hg18", A, B, C)
    
    def testJoin11(self):
        """reverse of regression testJoin10, where second block got lost
        """
        A = """
        a score=1000.0 tree=\"(panTro1.chr6:0.3,baboon.chr6:0.2)hg18.chr7;\"
        s panTro1.chr6 28862317 6 + 161576975 TAAAGA
        s baboon.chr6    241163 3 +   4622798 T---GA
        s hg18.chr7    27699739 3 + 158545518 T---GA
        """
        B = """
        a score=10.0 tree=\"(hg18.chr7:0.1,mm4.chr6:0.15)rn3.chr4;\"
        s hg18.chr7    27699739 3 + 158545518 T---GA
        s mm4.chr6     53303881 6 + 151104725 TAAAGA
        s rn3.chr4     81444246 6 + 187371129 taagga

        a score=10.0 tree=\"(mm4.chr6:0.15)rn3.chr4;\"
        s mm4.chr6     54303882 5 + 151104725 AAAG-A
        s rn3.chr4     81444247 6 + 187371129 aaggaa

        a score=10.0 tree=\"(mm4.chr8:0.15)rn3.chr4;\"
        s mm4.chr8     54303880 11 + 151104725 CATTCCTTAAC
        s rn3.chr4     105926875 9 + 187371129 c-ttcctta-c
        """
        C = """
        a score=0.000000 tree="((baboon.chr6:0.2,panTro1.chr6:0.3)hg18.chr7:0.1,mm4.chr6:0.15,mm4.chr6:0.15)rn3.chr4;"
        s baboon.chr6    241163 3 +   4622798 T------GA-
        s panTro1.chr6 28862317 6 + 161576975 TAAA---GA-
        s hg18.chr7    27699739 3 + 158545518 T------GA-
        s mm4.chr6     53303881 6 + 151104725 T---AAAGA-
        s mm4.chr6     54303882 5 + 151104725 ----AAAG-A
        s rn3.chr4     81444246 7 + 187371129 t---aaggaa

        a score=0.000000 tree="(mm4.chr8:0.15)rn3.chr4;"
        s mm4.chr8  54303880 11 + 151104725 CATTCCTTAAC
        s rn3.chr4 105926875  9 + 187371129 c-ttcctta-c
        """
        self.mafJoinTest("hg18", A, B, C)
    
    def testJoin12(self):
        """MAFs with no trees and multiple leaves
        """
        A = """
        a score=2.0
        s hg18.chr7    27707221 13 + 158545518 gcagctgaaaaca
        s rn4.chr7        07221 13 + 158545518 gcaGCTGAAaaca
        s baboon.chr6    249182 13 -   4622798 gcagctgaaaaca
        """
        B = """
        a score=5.0
        s hg18.chr7    27707221 13 + 158545518 gcagctgaaaaca
        s mm4.chr6     53310102 13 - 151104725 ACAGCTGAAAATA
        """
        C = """
        a score=0.000000 tree="(baboon.chr6:0.1,mm4.chr6:0.1,rn4.chr7:0.1)hg18.chr7;"
        s baboon.chr6   249182 13 -   4622798 gcagctgaaaaca
        s mm4.chr6    53310102 13 - 151104725 ACAGCTGAAAATA
        s rn4.chr7        7221 13 + 158545518 gcaGCTGAAaaca
        s hg18.chr7   27707221 13 + 158545518 gcagctgaaaaca
        """
        self.mafJoinTest("hg18", A, B, C, treelessRoot1="hg18", treelessRoot2="hg18")
          
    def testJoin13(self):
        """check for detecting overlapping components in a block."""
        A = """
        a score=0
        s sHuman-sChimp.chr1 200 10 + 1024 ACGTACGTAC
        s simHuman.chr1 825 10 - 1024 ACGTACGTAC
        s sHuman-sChimp.chr1 200 10 + 1024 ACGTACGTAC
        s simHuman.chr1 200 10 + 1024 ACGTACGTAC
        """
        B = """
        """
        C = """
        """
        self.mafJoinTest("sHuman-sChimp", A, B, C, treelessRoot1="sHuman-sChimp", treelessRoot2="sHuman-sChimp", expectExitCode=255, expectStderr="overlapping root components detected with in a block: sHuman-sChimp.chr1:200-210 (+) and sHuman-sChimp.chr1:200-210 (+)\n")

    def testJoin14(self):
        """Joining tandem dup with deletion in a block"""
        A = """
        # tandem dup                    
        a score=0.0                     
        s AB.chr1    200 6 + 1024 ACGTAC
        s A.chr1     200 6 + 1024 ACGTAC
        s A.chr1     206 6 + 1024 ACGTAC

        # deletion                      
        a score=0.0                     
        s AB.chr1    206 6 + 1024 GTACGT
        s A.chr1     306 3 + 1024 G---GT
        """
        B = """
        # duplication with insertion
        a score=0.0
        s AB.chr1  200 12 + 1024 ACG---TACGTACGT
        s B.chr1   200  9 + 1024 ACGTTTTAC------
        s B.chr1   306  6 + 1024 ---------GTACGT
        """
        C = """
        a score=0.000000 tree="(A.chr1:0.1,A.chr1:0.1,A.chr1:0.1,B.chr1:0.1,B.chr1:0.1)AB.chr1;"
        s A.chr1  200  6 + 1024 ACG---TAC------
        s A.chr1  206  6 + 1024 ACG---TAC------
        s A.chr1  306  3 + 1024 ---------G---GT
        s B.chr1  200  9 + 1024 ACGTTTTAC------
        s B.chr1  306  6 + 1024 ---------GTACGT
        s AB.chr1 200 12 + 1024 ACG---TACGTACGT
        """
        self.mafJoinTest("AB", A, B, C, treelessRoot1="AB", treelessRoot2="AB")

    def testJoin15(self):
        """Non-dup join, merging of blocks, adjacent references with no overlap.
        """
        A = """
        a score=5.0 tree=\"(mm4.chr6:0.15)hg18.chr7;\"
        s mm4.chr6     53310102 2 - 151104725 AC
        s hg18.chr7    27707221 2 + 158545518 gc
        
        a score=5.0 tree=\"(mm4.chr6:0.15)hg18.chr7;\"
        s mm4.chr6     53310104 11 - 151104725 AGCTGAAAATA
        s hg18.chr7    27707223 11 + 158545518 agctgaaaaca
        """
        B = """
        a score=2.0 tree=\"((panTro1.chr6:0.3)baboon.chr6:0.2)hg18.chr7;\"
        s panTro1.chr6 28869787 2 + 161576975 gc
        s baboon.chr6    249182 2 -   4622798 gc
        s hg18.chr7    27707221 2 + 158545518 gc
        
        a score=2.0 tree=\"((panTro1.chr6:0.3)baboon.chr6:0.2)hg18.chr7;\"
        s panTro1.chr6 28869789 10 + 161576975 agc-gaaaaca
        s baboon.chr6    249184 10 -   4622798 agc-gaaaaca
        s hg18.chr7    27707223 11 + 158545518 agctgaaaaca
        """ 
        C = """
        a score=0.000000 tree="((panTro1.chr6:0.3)baboon.chr6:0.2,mm4.chr6:0.15)hg18.chr7;"
        s panTro1.chr6 28869787 12 + 161576975 gcagc-gaaaaca
        s baboon.chr6    249182 12 -   4622798 gcagc-gaaaaca
        s mm4.chr6     53310102 13 - 151104725 ACAGCTGAAAATA
        s hg18.chr7    27707221 13 + 158545518 gcagctgaaaaca
        """
        self.mafJoinTest("hg18", A, B, C)

    def testJoin16(self):
        """ Inconsistent bases in overlapping components to be meregd
        """
        A = """
        a score=10.0 tree="(mm4.chr6:0.15)rn3.chr4;"
        s mm4.chr6     54303885 10 + 151104725 AAAAAAgggg
        s rn3.chr4     81444250 10 + 187371129 aaaaaagggg

        a score=10.0 tree="(mm4.chr6:0.15)rn3.chr4;"
        s mm4.chr6     54303893 12 + 151104725 ccggggAAAAAA
        s rn3.chr4     81444258 12 + 187371129 ccggggaaaaaa
        """
        B = """
        """
        C = """
        """
        self.mafJoinTest("sHuman-sChimp", A, B, C, treelessRoot2="sG-sH-sC", expectExitCode=255, expectStderrRe="^inconsistent sequences components being merged at column 8.*")

    def getTestJoin17A(self):
        "get MAF a for testJoin17* tests for -maxBlkWidth"
        return """
        a score=10.0 tree="(hg18.chr7:0.1,mm4.chr6:0.15)rn3.chr4;"
        s hg18.chr7    27699739 3 + 158545518 T---GA
        s mm4.chr6     53303881 6 + 151104725 TAAAGA
        s rn3.chr4     81444246 6 + 187371129 taagga

        a score=10.0 tree="(mm4.chr6:0.15)rn3.chr4;"
        s mm4.chr6     54303882 5 + 151104725 AAAG-A
        s rn3.chr4     81444247 6 + 187371129 aaggaa

        a score=10.0 tree="(mm4.chr6:0.15)rn3.chr4;"
        s mm4.chr6     54303885 10 + 151104725 AAAAAAgggg
        s rn3.chr4     81444250 10 + 187371129 aaaaaagggg

        a score=10.0 tree="(mm4.chr6:0.15)rn3.chr4;"
        s mm4.chr6     54303893 12 + 151104725 ggggAAAAAAgg
        s rn3.chr4     81444258 12 + 187371129 ggggaaaaaagg
        """

    def testJoin17a(self):
        """ test growing from overlapping blocks: no limit
        """
        B = """
        """
        C = """
        a score=0.000000 tree="(hg18.chr7:0.1,mm4.chr6:0.15,mm4.chr6:0.15,mm4.chr6:0.15)rn3.chr4;"
        s hg18.chr7 27699739  3 + 158545518 T---GA------------------
        s mm4.chr6  53303881  6 + 151104725 TAAAGA------------------
        s mm4.chr6  54303882  5 + 151104725 -AAAG-A-----------------
        s mm4.chr6  54303885 20 + 151104725 ----AAAAAAggggggAAAAAAgg
        s rn3.chr4  81444246 24 + 187371129 taaggaaaaaggggggaaaaaagg
        """
        self.mafJoinTest("sHuman-sChimp", self.getTestJoin17A(), B, C, treelessRoot2="sG-sH-sC")
    
    def FIXME_testJoin17b(self):
        """ test growing from overlapping blocks: 12 column limit
        """
        B = """
        """
        C = """
        a score=0.000000 tree="(hg18.chr7:0.1,mm4.chr6:0.15,mm4.chr6:0.15,mm4.chr6:0.15)rn3.chr4;"
        s hg18.chr7 27699739  3 + 158545518 T---GA--------
        s mm4.chr6  53303881  6 + 151104725 TAAAGA--------
        s mm4.chr6  54303882  5 + 151104725 -AAAG-A-------
        s mm4.chr6  54303885  8 + 151104725 ----AAAAAAgg--
        s rn3.chr4  81444246 14 + 187371129 taaggaaaaagggg

        a score=0.000000 tree="(mm4.chr6:0.15)rn3.chr4;"
        s mm4.chr6 54303893 12 + 151104725 ggggAAAAAAgg
        s rn3.chr4 81444258 12 + 187371129 ggggaaaaaagg
        """
        self.mafJoinTest("sHuman-sChimp", self.getTestJoin17A(), B, C, treelessRoot2="sG-sH-sC", maxBlkWidth=12)

    def testJoin18(self):
        """Merge of components in a block that went very wrong
        """
        A = """
        a score=50.0 tree="(hg18.chr7:0.1,mm4.chr6:0.15)rn3.chr4;"
        s hg18.chr7    27578828 38 + 158545518 AcG-tAcGtAcGtAcGtAcGtAc---cGtAcGtAcGtAcGtA
        s mm4.chr6     53215344 22 + 151104725 -cGgtAcGtAcGtAcGtAcGtAc-------------------
        s rn3.chr4     81344243 40 + 187371129 -cG-tAcGtAcGtAcGtAcAtAcGtAcGtAcGtAcGtAcGtA

        a score=50.0 tree="(mm4.chr6:0.15)rn3.chr4;"
        s mm4.chr6     53215366 16 + 151104725 ----------------------cGtAcGtAcGtAcGtA
        s rn3.chr4     81344241 38 + 187371129 tAcGtAcGtAcGtAcGtAcGtAcGtAcGtAcGtAcGtA
        """
        B = """
        """
        C = """
        a score=0.000000 tree="(hg18.chr7:0.1,mm4.chr6:0.15,mm4.chr6:0.15)rn3.chr4;"
        s hg18.chr7 27578828 38 + 158545518 A--cG-tAcGtAcGtAcGtAcGtAc---cGtAcGtAcGtAcGtA
        s mm4.chr6  53215344 22 + 151104725 ---cGgtAcGtAcGtAcGtAcGtAc-------------------
        s mm4.chr6  53215366 16 + 151104725 ------------------------cGtAcGtAcGtAcGtA----
        s rn3.chr4  81344241 42 + 187371129 -tAcG-tAcGtAcGtAcGtAcAtAcGtAcGtAcGtAcGtAcGtA
        """
        self.mafJoinTest("hg18", A, B, C)
    
    def testJoin19(self):
        """Merge of components with an inconsistent alignment of a common base
        """
        A = """
        a score=50.0 tree="(hg18.chr7:0.1)rn3.chr4;"
        s hg18.chr7    27578828 38 + 158545518 AAA-GGGAATGTTAACCAAATGA---ATTGTCTCTTACGGTG
        s rn3.chr4     81344243 40 + 187371129 -AA-GGGGATGCTAAGCCAATGAGTTGTTGTCTCTCAATGTG

        a score=50.0 tree="(hg18.chr7:0.1)rn3.chr4;"
        s hg18.chr7    27578828 34 + 158545518 AAA-GGGAATGTTAACCAAATG--A-ATTGTCTCTTAC----
        s rn3.chr4     81344243 40 + 187371129 -AA-GGGGATGCTAAGCCAATGAGTTGTTGTCTCTCAATGTG
        """
        B = """
        """
        C = """
        a score=0.000000 tree="(hg18.chr7:0.1,hg18.chr7:0.1)rn3.chr4;"
        s hg18.chr7 27578828 34 + 158545518 -AAA--GGGAATGTTAACCAAATG--A-ATTGTCTCTTAC----
        s hg18.chr7 27578828 38 + 158545518 A-AA--GGGAATGTTAACCAAATGA---ATTGTCTCTTACGGTG
        s rn3.chr4  81344243 40 + 187371129 --AA--GGGGATGCTAAGCCAATGAGTTGTTGTCTCTCAATGTG
        """
        self.mafJoinTest("hg18", A, B, C)
    
# FIXME: should be controllable from the command line
#import logging
#logger.setLevel(logging.INFO)
if __name__ == '__main__':
    unittest.main()
