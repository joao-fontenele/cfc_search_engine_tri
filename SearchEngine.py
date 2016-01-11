#!/usr/bin/env python
#coding: utf-8

from __future__ import division
from Parser import Parser
from collections import Counter
from math import log
from util import Document
from util import Query
import Evaluator
import ast
import heapq
import os
import re
import sys

class SearchEngine(object):
    def __init__(self):
        """
        Constructor method.
        """
        self.invertedIndex = dict()
        self.documents = dict()
        stopWordsPath = "sw.txt"
        self.parser = Parser(stopWordsPath)

    def calculateWeights(self):
        """
        Calculate the idf and tf-idf weights using the self.invertedIndex dict.

        tf = term frequency of the word in the document.
        idf = log_2(N/n), where N is the amount of words in the collection, and
        n is the amount of documents in wich the word appears.
        tf-idf = tf * idf. It's the weight of a word in a document.

        This method expects that the inverted index contains frequecy of the
        words, and does not attempt to check if the current values are in fact
        frequencies.  So the user must be aware if there's or not really
        frequencies in the index before calling this method, at the risk of
        getting wrong weights and losing the previous data.

        return: None
        """
        # N is the amount of words in the collection
        N = len(self.documents)
        for word in self.invertedIndex.iterkeys():
            idf, lst = self.invertedIndex[word]
            # n is the amount of documents in wich the word appeared
            n = len(lst)
            #print "word: {}  N: {}  n: {}".format(word, N , n)
            idf = log(N / n, 2) # idf of the word
            # now calculate the weight for each pair document, frequency
            for iii, pair in enumerate(lst):
                docID, freq = pair
                weight = idf * freq
                lst[iii] = (docID, weight)
            self.invertedIndex[word] = (idf, lst)

    def calculateDocNorms(self):
        """
        Calculate the leghts/norms of the document vectors, using the weights
        in the inverted index. And places them at the self.documents dict, on
        the Document.norm field.

        It calculates the norm based on the current weights in the inverted
        index. This method does not attempt to check if the weights used are
        valid or not.

        return: None
        """
        # sum the square of the weight of each component of the each document
        # vector
        for word, pair in self.invertedIndex.iteritems():
            idf, lst = pair
            for docId, weight in lst:
                doc = self.documents[docId]
                subTotal = doc.norm
                subTotal += weight **2
                doc = doc._replace(norm=subTotal)

                # place the result in the self.documents dict
                self.documents[docId] = doc

        # now that we have the sum of the squares, we take the square root
        # to get the norm
        for docId in self.documents.iterkeys():
            doc = self.documents[docId]
            doc = doc._replace(norm=doc.norm **0.5)
            self.documents[docId] = doc

    def createIndex(self, folderPath, regex=r"^cf\d{2}$", tfidf=True):
        """
        Creates the inverted index based on the files of the folderPath, that
        match the regex.

        The parseFile method is collection specific, and could be overrided.
        In this case it's using the CFC collection. In the case the file match
        the regex but is either a folder or cannot be opened, it's ignored.

        param folderPath: string containing the path to the folder with the
        collection. Defaults to the current working directory.
        param regex: string containing a regex to match the files in the folder
        that will be parsed. Defaults to a regex for the CFC collection.
        param tfIdf: bool value, if it's True, calculate the idf for the words
        int the self.invertedIndex dict, and the tf-idf weights for the words
        in the documents. Defaults to True.
        return: None.
        """
        print("Creating index using the files in the folder: {}" .format(folderPath))

        # regex to match the files of the collection.
        validFile = re.compile(regex)
        # list the files and folders in the folderPath variable, and the ones
        # that match the regex are parsed
        for fileName in os.listdir(folderPath):
            if validFile.match(fileName):
                path = os.path.join(folderPath, fileName)
                if not os.path.isfile(path): continue
                # get the the doc details, and word frequencies for each
                # document in the file
                for doc, wordCounter in self.parser.parseFile(path):
                    # add the document details to the self.documents dict
                    self.documents[doc.id] = doc

                    # now we add the words to the index
                    for word, freq in wordCounter.items():
                        idf, lst = self.invertedIndex.get(word, (0, []))
                        lst.append((doc.id, freq))
                        self.invertedIndex[word] = (idf, lst)
        if tfidf:
            # update self.invertedIndex with tf-idf weights, while also
            # calculating the idf of the words
            self.calculateWeights()

        # update the self.documents with norms of the documents
        self.calculateDocNorms()

    def evaluateResults(self, query, results):
        """
        A method to get evaluation metrics from the results to the query.

        Metrics and usefull data are returned inside a dict:
            key "recallPoints": has a list of interpolated recall points.
            key "MAP": has the MAP metric on the recall points.
            key "P@10": has the precision on point 10 metric.

        param query: util.Query object representing the query. The relevants
        field must not be empty.
        param results: a list with the results to the query, the list is formed
        by tuples of the kind(similarity, util.Document).
        return: a dict containing usefull data about the evaluation of the
        result. More detail above.
        """
        relevants = query.relevants
        assert relevants
        assert results

        # get a list with the ids of the documents of the result
        resultIds = [doc.id for sim, doc in results]

        # calculate non interpolated recall point and precision at point 10
        pair = Evaluator.getRecallPointsAndPrecisionAt(relevants, resultIds, point=10)
        recallPoints, pAtTen = pair

        # interpolate recall points to get exactly 11 points
        iRecallPoints = Evaluator.interpolateRecallPoints(recallPoints)

        # we ignore the recall point with recall of zero (slides Baeza-Yates)
        # to calculate interpolated MAP
        MAP = Evaluator.calculateMAP(recallPoints[1:])

        # place usefull data in a dict
        evalResults = {}
        evalResults["recallPoints"] = iRecallPoints
        evalResults["P@10"] = pAtTen
        evalResults["MAP"] = MAP
        return evalResults

    def loadIndex(self, path):
        """
        Loads the self.documents and self.invertedIndex dicts data from a file
        created with the self.saveIndex method.

        If it fails to open the file the exception is not handled.

        param path: string containing the path to file to load.
        return: None.
        """
        print ("Loading index from the file: {}".format(path))
        fin = open(path)

        # regex for parsing the self.documents
        docRegex = re.compile(r"(?P<id>\d+);(?P<year>\d+);(?P<title>.+);(?P<authors>.+)?;(?P<norm>.+)")
        # parsing the documents data
        for line in fin:
            line = line.strip()
            # if there's something in the line it must be data about a document
            if line:
                # if the line starts with a # ignore it
                if not line.startswith("#"):
                    match = docRegex.match(line)
                    docId = int(match.group("id"))
                    year = match.group("year")
                    title = match.group("title")
                    authors = match.group("authors")
                    norm = float(match.group("norm"))

                    self.documents[docId] = Document(docId, year, title, authors, norm)
            # if there's an empty line the documents part have ended
            else:
                break

        # regex for parsing the self.invertedIndex
        indexRegex = re.compile(r"(?P<word>.+);(?P<idf>.+);(?P<lst>.+)")
        # parsing the inverted index data
        for line in fin:
            line = line.strip()
            if not line.startswith("#"):
                match = indexRegex.match(line)
                word = match.group("word")
                idf = float(match.group("idf"))
                lst = ast.literal_eval(match.group("lst"))
                pair = (idf, lst)
                self.invertedIndex[word] = pair
        fin.close()

    def processQuery(self, query, K=10, evaluate=False):
        """
        Given an util.Query object returns the top K documents most similar
        according to the vector model, and evaluation results if param evaluate
        is True.

        param query: util.Query object.
        param K: get the K most similar documents.
        param evaluate: whether or not to evaluate the results of the query.
        return: a pair (results, evalResulst), where results is a list of
        tuples (similarity, util.Document) ordered in decrescent similarity,
        and evalResults is a dict with data on the evaluation.
        """
        words = self.parser.tokenize(query.queryString)
        qCounter = Counter(words)

        accumulators = {}

        for word in qCounter.iterkeys():
            # in the case a word in the query doesn't exist in the inverted
            # index the word in the query is ignored
            try:
                idf, lst  = self.invertedIndex[word]
            except KeyError:
                print("[*] The word '{}' doesn't exist in the inverted index and will be ignored.".format(word))
                continue
            qCounter[word] = qCounter[word] * idf
            for pair in lst:
                docId, weight = pair
                partialAcc = accumulators.get(docId, 0)
                partialAcc += weight * qCounter[word]
                accumulators[docId] = partialAcc

        # more efficient way of getting the top K similarities without having
        # to sort all the results
        heap = [] # min heap to keep the top K similarities
        for docId, acc in accumulators.iteritems():
            doc = self.documents[docId]
            # normalize the accumulator for the doc with the doc length, at
            # this point acc holds the final similarity value with the query
            acc = acc / doc.norm
            # if the heap is not full, add the similarity regardless
            if len(heap) < K:
                heapq.heappush(heap, (acc, doc))
            # the heap is full, but the current similarity is greater than the
            # smallest similarity in the heap, so we pop the min heap to remove
            # the smallest and add the current similarity to the top K
            elif acc > heap[0][0]:
                minAcc, minDoc = heapq.heappop(heap)
                heapq.heappush(heap, (acc, doc))
            # else the current similarity is smaller than the smallest
            # similarity in the heap, so we ignore the current one
            else:
                continue

        #assert len(heap) == K, "len(heap) = {}".format(len(heap))

        # now we get the ordered ranking, from the heap, results will be a pair
        # of (similarity, util.Document)
        result = []
        while heap:
            pair = heapq.heappop(heap)
            result.append(pair)

        # reverse the results so that the document with greatest similarity is
        # at the top of the answer
        result.reverse()

        evalResults = None
        # if the param evaluate is True we evaluate the results
        if evaluate:
            evalResults = self.evaluateResults(query, result)

        return result, evalResults

    def saveIndex(self, path):
        """
        Saves the self.documents and self.invertedIndex dicts, in a human
        readable form to the specified path.

        If it fails in opening the file the exception is not handled

        param path: string containing the path of the file in which the dicts
        will be saved
        return: None
        """
        print("Saving index in the file: {}.".format(path))
        with open(path, "w") as fout:
            fout.write("# dados dos documentos\n# id;ano;titulo;autores;norma\n")
            for docID, doc in self.documents.iteritems():
                fout.write("{};{};{};{};{}\n".format(doc.id, doc.year, doc.title, doc.authors, doc.norm))

            fout.write("\n# índice invertido\n# palavra;idf;listaInvertida(docID, peso)\n")
            for word, pair in self.invertedIndex.iteritems():
                idf, lst = pair
                fout.write("{};{};{}\n".format(word, idf, lst))

if __name__ == '__main__':
    e = SearchEngine()

    #e.documents = {1: Document(1, 1, "t1", "a1", 0), 2: Document(2, 2, "t2", "a2", 0), 3: Document(3, 3, "t3", "a3", 0), 4: Document(4, 4, "t4", "a4", 0)}
    #e.invertedIndex = {"A": (0, [(1, 3), (2, 2), (3, 2)]), "B": (0, [(1, 1), (4, 2)]), "C": (0, [(2, 1)])}
    #e.calculateWeights()

    path = 'completa'
    #path = 'teste'
    e.createIndex(path)

    e.saveIndex("t1_index.txt")
    #e.loadIndex("t1_index.txt")
    for q in e.parser.parseQueryFile("completa/cfquery"):
    #qs = [Query(1, "clinical values", [2, 355]), Query(2, "patients normal", [1, 2, 3])]
    #for q in qs:
        res, evalRes = e.processQuery(q, 10, evaluate=True)
        print(q.id, q.queryString)
        print("relevants", q.relevants)
        for r in res:
            print('\t*', r)
        print(evalRes)
        print('\n')

    #s = SearchEngine()
    #s.loadIndex("t1_index.txt")
    #s.saveIndex("t2_index.txt")

    #for word, pair in s.invertedIndex.iteritems():
    #    print word
    #    idf, lst = pair
    #    print "\t idf: {}".format(idf)
    #    print "\t weights: {}".format(lst)
    #    print ''
