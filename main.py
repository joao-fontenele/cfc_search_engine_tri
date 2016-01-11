#!/usr/bin/env python
#coding: utf-8

from __future__ import division
from SearchEngine import SearchEngine
from time import time as getTime
#from time import clock as getTime
from util import Query
import Evaluator
import argparse
import sys

CREATE_INDEX_CMD = "createindex"
INTERACTIVE_QUERY_CMD = "iquery"
PROCESS_QUERY_FILE_CMD = "queryfile"
RANKING_SIZE = 20

INDEX_PATH = "cfcIndex.txt"

def createParser():
    description = """
        Search engine implementation for the CFC collection. For the
        'Tópicos em Recuperação de Informação' course at UFAM 2015/2"""
    parser = argparse.ArgumentParser(description=description)
    functionHelp = """
        function can be either:
        <{}> for creating the index;
        <{}> for an interactive query mode;
        <{}> for parsing a cfc query file.
        """.format(CREATE_INDEX_CMD, INTERACTIVE_QUERY_CMD,
            PROCESS_QUERY_FILE_CMD)
    rsHelp = """
        optional argument for specifying the amont of documents that
        should be returned by a query, defaults to {}
        """.format(RANKING_SIZE)
    inHelp = """
        argument for passing input path to the program, needed by the
        {}, and {} functionalities.
        """.format(CREATE_INDEX_CMD, PROCESS_QUERY_FILE_CMD)

    parser.add_argument("function", help=functionHelp)
    parser.add_argument("-in", "--input", help=inHelp, dest="path")
    parser.add_argument("-rs", "--rankingsize", help=rsHelp,
            type=int, default=RANKING_SIZE, dest="rSize")

    return parser

def loadIndexWrapper(eng):
    try:
        start = getTime()
        eng.loadIndex(INDEX_PATH)
        print("It took {:.5f} s to load the index."
                .format(getTime() - start))
    except IOError:
        print("Could not read the index at path: {}".format(INDEX_PATH))
        print("Please create the index first with argument '{}'."
                .format(CREATE_INDEX_CMD))
        sys.exit(-1)
    return eng

def menuCreateIndex(eng, cfcFolder):
    if not cfcFolder:
        print("Please enter the path to the cfc collection files using the -in argument")
        sys.exit(-1)

    try:
        eng.createIndex(cfcFolder)
    except IOError as e:
        print("There was an error while parsing the files in the folder: {}"
                .format(collectionFolder))
        print("Please make sure there are cfc files in the folder path.")
        print(e.message)
    try:
        eng.saveIndex(INDEX_PATH)
    except IOError as e:
        print("Could not save the index file at path: {}".format(INDEX_PATH))
        print(e.message)

def menuInteractiveQuery(eng, rankingSize):
    eng = loadIndexWrapper(eng)

    qId = 1
    while True:
        try:
            queryString = raw_input(">> ")
        except EOFError:
            print('')
            break
        except KeyboardInterrupt:
            print('')
            break
        query = Query(qId, queryString, [])

        start = getTime()
        results, evalResults = eng.processQuery(query, rankingSize)
        print("It took {} s to process the query."
                .format(getTime() - start))

        for result in results:
            similarity, doc = result
            print("similarity: {}. id: {}"
                    .format(similarity, doc.id))
            print("\ttitle: {}".format(doc.title))
            print("\tauthors: {}, year: {}\n"
                    .format(doc.authors, doc.year))

def menuQueryFile(eng, queryFile, rankingSize):
    eng = loadIndexWrapper(eng)

    if not queryFile:
        print("Please enter the path to the cfc query file using the -in argument")
        sys.exit(-1)

    print("ranking size: {}".format(rankingSize))

    MAPs = []
    recallPointsLst = []
    pAtTens = []
    times = []
    try:
        print("query id ; P@10 ; interpolated MAP ; time (s)")
        for query in eng.parser.parseQueryFile(queryFile):
            start = getTime()
            results, evalResults = eng.processQuery(query, rankingSize,
                    evaluate=True)
            end = getTime() - start

            MAPs.append(evalResults["MAP"])
            recallPointsLst.append(evalResults["recallPoints"])
            pAtTens.append(evalResults["P@10"])
            times.append(end)
            print("{:03d} ; {:.5f} ; {:.5f} ; {:.5f} "
                    .format(query.id, pAtTens[-1], MAPs[-1], times[-1]))
    except IOError as e:
        print("Could not open the cfc query file at: {}.".format(queryFile))
        print(e.message)
        sys.exit(-1)

    avgRecallPoints = Evaluator.getAverageRecallPoints(recallPointsLst)
    avgMAP = sum(MAPs) / len(MAPs)
    avgPAtTen = sum(pAtTens) / len(pAtTens)
    avgTime = sum(times) / len(times)
    print("\nAverages:")

    print("\tP@10: {:.5f}".format(avgPAtTen))
    print("\tinterpolated MAP: {:.5f}".format(avgMAP))
    print("\ttime: {:.5f} s".format(avgTime))

    print("\tinterpolated recall points (precision, recall):")
    for pair in avgRecallPoints:
        p, r = pair
        print("\t({:.5f}, {:.5f}),".format (p, r))

if __name__ == '__main__':
    parser = createParser()
    args = parser.parse_args()
    eng = SearchEngine()

    if args.function == CREATE_INDEX_CMD:
        collectionFolder = args.path
        start = getTime()
        menuCreateIndex(eng, collectionFolder)
        print("It took {} s to create and save the index."
                .format(getTime() - start))

    elif args.function == INTERACTIVE_QUERY_CMD:
        rankingSize = args.rSize
        menuInteractiveQuery(eng, rankingSize)

    elif args.function == PROCESS_QUERY_FILE_CMD:
        queryFile = args.path
        rankingSize = args.rSize
        start = getTime()
        menuQueryFile(eng, queryFile, rankingSize)
        print("It took {} s to load the index and process all the queries."
                .format(getTime() - start))
    else:
        parser.print_help()
        #parser.print_usage()

