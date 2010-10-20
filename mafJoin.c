#include "common.h"
#include "options.h"
#include "genome.h"
#include "malnSet.h"
#include "malnJoinDups.h"
#include "malnJoinSets.h"
#include "malnMergeComps.h"
#include "sonLibETree.h"
#include "malnMultiParents.h"
#include <limits.h>

/*
 * Notes: 
 *  - this would probably be simpler (and for sure more efficient) if
 *    it was done with block based rather than column based merges.
 */

static bool debug = false;  // FIXME: tmp

/* set to true to cleanup all memory for memory leak checks */
static bool memLeakDebugCleanup = true;

/* command line option specifications */
static struct optionSpec optionSpecs[] = {
    {"branchLength", OPTION_DOUBLE},
    {"treelessRoot1", OPTION_STRING},
    {"treelessRoot2", OPTION_STRING},
    {"maxBlkWidth", OPTION_INT},
    {"help", OPTION_BOOLEAN},
    {NULL, 0}
};

static char *usageMsg =
    "mafJoin [options] refGenome inMaf1 inMaf2 outMaf\n"
    "\n"
    "Options:\n"
    "  -help\n"
    "  -branchLength=0.1 - branch length to use when generating\n"
    "   a trees for MAF. Defaults to 0.1.\n"
    "  -treelessRoot1=genome - root genome for inMaf1 blocks\n"
    "   that do not have trees (see below).\n"
    "  -treelessRoot2=genome - root genome for inMaf2 blocks\n"
    "   that do not have trees.\n"
    "  -maxBlkWidth=n - set a cutoff on the maximum width of an alignment\n"
    "   block when join blocks.  This is used to limit joining of blocks\n"
    "   near the Evolover root were long, contiguous overlapping regions\n"
    "   can cause exponential growth in run time and memory requirements\n"
    "\n"
    "If MAF blocks (mafAli) don't have a tree associated with them, one\n"
    "will be created.  The root genome for the tree is chosen based on\n"
    "the genome specified by the -treelessRoot1 or -treelessRoot2 options.\n"
    "One sequence from that genome becomes the root and the remainder\n"
    "become it's direct children.\n";

/* usage msg and exit */
static void usage(char *msg) {
    errAbort("Error: %s\n%s", msg, usageMsg);
}

/* load a MAF and do internal joining.  */
static struct malnSet *loadMaf(struct Genomes *genomes, char *inMaf, double defaultBranchLength,
                               char *treelessRootName, int maxBlkWidth, char *setName) {
    struct Genome *treelessRootGenome = (treelessRootName != NULL) ? genomesObtainGenome(genomes, treelessRootName) : NULL;
    struct malnSet *malnSet = malnSet_constructFromMaf(genomes, inMaf, defaultBranchLength, treelessRootGenome);
    if (debug) {
        malnSet_dump(malnSet, stderr, "%s input", setName);
    }
    malnJoinDups_joinSetDups(malnSet);
    if (debug) {
        malnSet_dump(malnSet, stderr, "%s: joined-dups", setName);
    }
    malnMultiParents_check(malnSet);
    return malnSet;
}

/* join two mafs */
static void mafJoin(char *refGenomeName, char *inMaf1, char *inMaf2, char *outMaf, double defaultBranchLength,
                    char *treelessRoot1Name, char *treelessRoot2Name, int maxBlkWidth) {
    struct Genomes *genomes = genomesNew();
    struct Genome *refGenome = genomesObtainGenome(genomes, refGenomeName);

    struct malnSet *malnSet1 = loadMaf(genomes, inMaf1, defaultBranchLength, treelessRoot1Name, maxBlkWidth, "set1");
    struct malnSet *malnSet2 = loadMaf(genomes, inMaf2, defaultBranchLength, treelessRoot2Name, maxBlkWidth, "set2");

    // join and then merge overlapping blocks that were created
    struct malnSet *malnSetJoined = malnJoinSets(refGenome, malnSet1, malnSet2, maxBlkWidth);
    if (debug) {
        malnSet_dump(malnSetJoined, stderr, "out: joined");
    }
    malnJoinDups_joinSetDups(malnSetJoined);
    if (debug) {
        malnSet_dump(malnSetJoined, stderr, "out: joined-dups");
    }
    malnMergeComps_merge(malnSetJoined);
    if (debug) {
        malnSet_dump(malnSetJoined, stderr, "out: merged");
    }
    malnMultiParents_check(malnSetJoined);
    malnSet_writeMaf(malnSetJoined, outMaf);

    if (memLeakDebugCleanup) {
        malnSet_destruct(malnSet1);
        malnSet_destruct(malnSet2);
        malnSet_destruct(malnSetJoined);
        genomesFree(genomes);
    }
}

/* Process command line. */
int main(int argc, char *argv[]) {
    optionInit(&argc, argv, optionSpecs);
    if (optionExists("help")) {
        usage("Usage:");
    }
    if (argc != 5)  {
        usage("Error: wrong number of arguments");
    }

    if (optionExists("maxBlkWidth")) {
        errAbort("-maxBlkWidth not implemented");
    }

    mafJoin(argv[1], argv[2], argv[3], argv[4], optionDouble("branchLength", 0.1), 
            optionVal("treelessRoot1", NULL), optionVal("treelessRoot2", NULL),
            optionInt("maxBlkWidth", INT_MAX));
    return 0;
}
