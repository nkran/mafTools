include inc/common.mk

##############################
# These modules are dependent and are
# only included if their depedencies exist!
ifeq ($(wildcard ${sonLibPath}/../Makefile),)
	Comparator =
	TransitiveClosure =
	Stats =
	ToFasta =
	PairCoverage =
	Coverage =
$(warning Because dependency ${sonLibPath} is missing mafComparator, mafTransitiveClosure, mafStats, mafToFastaStitcher, mafPairCoverage, mafCoverage will not be built / tested / cleaned. See README.md for information about dependencies.)
else
	Comparator = mafComparator
	Stats = mafStats
	ToFasta = mafToFastaStitcher
	PairCoverage = mafPairCoverage
	Coverage = mafCoverage
ifeq ($(wildcard ../sonLib/lib/stPinchesAndCacti.a),)
	TransitiveClosure =
$(warning Because dependency ../pinchesAndCacti is missing mafTransitiveClosure will not be built / tested / cleaned. See README.md for information about dependencies.)
else
	TransitiveClosure = mafTransitiveClosure
endif # sonlib
endif # pinches
##############################
dependentModules= ${Comparator} ${TransitiveClosure} ${Stats} ${ToFasta} ${PairCoverage} ${Coverage}

modules = lib ${dependentModules} mafValidator mafPositionFinder mafExtractor mafSorter mafDuplicateFilter mafFilter mafStrander mafRowOrderer

.PHONY: all %.all clean %.clean test %.test
.SECONDARY:

all: ${modules:%=%.all}

%.all:
	cd $* && make all

clean: ${modules:%=%.clean}

%.clean:
	cd $* && make clean

test: ${modules:%=%.test} ${Warnings:%=%.warn}
	@echo 'mafTools tests complete.'

%.test:
	cd $* && make test
