#!/usr/bin/env python
#coding: utf-8

from collections import Counter
from util import Document
from util import Query
import re

class Parser:
    def __init__(self, stopWordsPath="sw.txt"):
        self.stopWords = self.readStopWords(stopWordsPath)

        self.cfcCollectionAttrs = [
                    "PN",       # paper number
                    "RN",       # doc id in the collection
                    "AN",       # super collection id i guess
                    "AU",       # authors
                    "TI",       # title
                    "SO",       # source
                    "MJ",       # major subjects
                    "MN",       # minor subjects
                    "AB",       # abstract when present, or excerpt otherwise
                    "EX",       # abstract when present, or excerpt otherwise
                    "RF",       # list of references used in the doc
                    "CT",       # citation list to the doc
                        ]
        self.cfcQueryAttrs = [
                    "QN",       # query number
                    "QU",       # proper query
                    "NR",       # number of relevant docs
                    "RD",       # relevant documents
                        ]

    def initializeLastItem(self, attrList, lastItem) :
        """
        Helper method, to reinitialize a dictionary containing the data from a
        CFC collection document or query. Used by the file parsers

        param doc: a dict.
        return: the reinitialized dict.
        """
        for attr in attrList:
            lastItem[attr] = ''
        lastItem["lastAttr"] = ''
        return lastItem

    def parseCFCFile(self, path, regex, lastItemAttrs, treatLastItemFunction):
        """
        CFC Collection specific file parser. It's a internal generic file
        parser, users should use the parseFile or parseQueryFile methods
        instead of this one.

        If it fails to open the file, does not attempt to treat the exception.

        param path: string containig the path to the file to parse.
        param regex: a string containing a regex to separate attributes and
        content.  The regex must contain a named attribute called "attr" and
        another called "content".
        param lastItemAttrs: a list containing the attributes of the items
        present in the file for usel of self.initializeLastItem method.
        param treatLastItemFunction: a function to be called when we finish
        parsing an item from the path. The function should receive a dict
        containing the data of the file, and return a result to be yielded by
        this method.
        yield: results of treatLastItemFunction for each item in the file on
        the param path.
        """
        fin = open(path)
        # helper funcion to reset the dict used for parsing the fin. Last doc
        # holds the temporary data of the current document being parsed
        lastItem = self.initializeLastItem(lastItemAttrs, {})

        for line in fin:
            line = line.strip()
            # if there's content in the line we haven't finished parsing a doc
            if line and fin:
                # add the content of the line to the correct attr in the
                # lastItem dict
                lastItem = self.parseLine(line, lastItem, regex)

            # else we finished reading a doc
            else:
                if self.isEmptyItem(lastItem): continue

                result = treatLastItemFunction(lastItem)
                lastItem = self.initializeLastItem(lastItemAttrs, lastItem)

                yield result
        fin.close()

    def parseFile(self, path):
        """
        Wrapper method for the self.parseCFCFile method, for parsing the proper
        file containng the documents from the CFC collection.

        Does not treat the exception that may be raised when opening the file
        in the path.

        param path: string containing the path to the file.
        yield: each query found in the file, the returned objects are tuples of
        the kind (util.Document, collections.Counter). The counter is a dict
        with word keys and frequency values.
        """
        print("Processing file: {}".format(path))
        # regex for separating the attributes of the document from content
        regex = r"^((?P<attr>(PN|RN|AN|AU|TI|SO|MJ|MN|AB|EX|RF|CT))\s+)?(?P<content>(.*\w+.*)*)"
        # attrs present in the cfc collection documents
        attrs = self.cfcCollectionAttrs
        # helper function to deal with the parsed data. Transforms the data
        # parsed in a tpuple of util.Document object and a Counter with the
        # frequency of the words in the document
        function = self.treatLastDoc
        for result in self.parseCFCFile(path, regex, attrs, function):
            yield result

    def parseLine(self, line, lastItem, regex):
        """
        Parse a single line of a CFC file, adding the content of the line to
        the last seen attribute.

        The regex should have a named field called "attr" and another
        "content". If an attr is found in the line, updates a "lastItem" entry
        in the lastItem dict, with the attr found.

        param line: a string containing the line to be parsed.
        param lastItem: a dict that will contain the temporary data of the item
        being parsed.
        param regex: a string containing a regex to parse the line. Must have a
        named fields "attr" and "content".

        return: the param lastItem dict, updated with the param line.
        """
        assert type(lastItem) == dict
        sep = re.compile(regex)
        # separate a possible attribute from content, with a regex
        match = sep.match(line)
        assert match

        # groups named in the sep regex
        attr = match.group("attr")
        content = match.group("content")

        # in the case there's an attribute in the line, we know we have
        # finished the last attribute we have seen, otherwise we append to
        # the last attribute seen
        if attr:
            lastItem["lastAttr"] = attr
        lastAttr = lastItem["lastAttr"]
        # assert lastAttr # buggy because of strange ^Z lines in the end of some files
        # add the content of the line to the lastAttr seen
        if lastAttr:
            lastItem[lastAttr] = (' '.join([lastItem[lastAttr], content.strip()])).strip()

        return lastItem

    def parseQueryFile(self, path):
        """
        Wrapper method for the self.parseCFCFile method, for parsing the query
        file from the CFC collection.

        Does not treat the exception that may be raised when opening the file
        in the path.

        param path: string containing the path to the file.
        yield: each query found in the file, the returned objects are
        util.Query objects.
        """
        # regex for separating the attributes from the content
        regex = r"^\s*(?P<attr>QN|QU|NR|RD)?\s*(?P<content>(.*\w+.*)*)"
        # list of attributes present in the cfc query file
        attrs = self.cfcQueryAttrs
        # helper function that deals with the data parsed and transforms it on
        # util.Query objects
        function = self.treatLastQuery
        for result in self.parseCFCFile(path, regex, attrs, function):
            yield result

    def tokenize(self, string, regex=r"[a-zA-Z']+"):
        """
        Get a list with the words in the string, while also removing the stop
        words defined in the creation of the class.

        param string: string with the content to be tokenized.
        param regex: string containing a regex of what is considered a word.

        return: a list of strings containing the non stop words words, from the
        string param.
        """
        # regex for separating the words in the content
        tokenizer = re.compile(regex)
        # get the words that match the regex and set them to lower case
        words = [word.lower() for word in tokenizer.findall(string)]

        # removal of the stop words defined in the __init__ method from the
        # list of words
        for sw in self.stopWords.intersection(words):
            while sw in words:
                words.remove(sw)

        return words

    def readStopWords(self, path):
        """
        Used in the __init__ method to load the stop words from a file.

        If the file is empty returns an empty set. The file must contain words
        separated by white space characters, and must be lower case. If it
        fails to open the file the exception is not handled.

        param path: string containing the path to the file containg the stop
        words.
        return: a set containig the stop words from the file
        """
        fin = open(path)

        # place the stop words in a set for faster access
        sws = set()
        for line in fin:
            line = line.strip()
            for word in line.split():
                sws.add(word.lower())
        fin.close()
        return sws

    def treatLastDoc(self, lastDoc):
        """
        Helper method that transforms the data in the lastDoc dict into a tuple
        of util.Document object and a Counter containing the frequencies of the
        words in the document

        param lastDoc: a dict containing the data parsed.
        return: a tuple(util.Document, collections.Counter). The counter is a
        dict with word keys and frequency values.
        """
        total = Counter()

        # the list of relevant attributes to tokenize. Tokenize also
        # removes stop words defined in the init method
        relevant = ["TI", "AB", "EX", "MJ", "MN"]
        for attr in relevant:
            content = lastDoc[attr]
            assert type(content) == str
            words = self.tokenize(content)
            counter = Counter(words)
            total +=  counter

        # form the Document object return
        docId = int(lastDoc["RN"])

        # get the year of publishment
        regex = r"(?P<year>\d{2})(?P<idInYear>\d{3})"
        sep = re.compile(regex)
        match = sep.match(lastDoc["PN"])
        year = int(match.group("year"))

        title = lastDoc["TI"]
        authors = lastDoc["AU"]
        tempNorm = 0 # irrelevant norm to be udated in the future
        doc = Document(docId, year, title, authors, tempNorm)

        result = doc, total
        return result

    def isEmptyItem(self, lastItem):
        """
        Helper method to know if the last item parsed is empty or not. Needed
        because some files have double empty lines between documents.

        param lastItem: a dict with the data of the last item parsed.

        return: True if the lastItem dict has a single key with a value that
        evaluates to True, False otherwise.
        """
        for key in lastItem.iterkeys():
            if lastItem[key]:
                return False
        return True

    def treatLastQuery(self, lastQuery):
        """
        Helper method that transforms the data in the lastQuery dict into an
        util.Query object.

        param lastQuery: a dict containg the data parsed.
        return: an util.Query object.
        """
        queryId = int(lastQuery["QN"])
        queryString = lastQuery["QU"]

        sep = re.compile(r"(?P<docId>\d+)\s*(?P<grades>\d+)")

        relevants = []
        for pair in sep.findall(lastQuery["RD"]):
            docId, grades = pair
            docId = int(docId)
            relevants.append(docId)

        return Query(queryId, queryString, relevants)

if __name__ == '__main__':
    p = Parser()
    for r in p.parseQueryFile("cfquery"):
        print(r,  '\n')
    #s = ' Salivary amylase levels were determined in normal subjects from birth until adult life and in children with conditions sometimes associated with low pancreatic amylase such as malnutrition, coeliac disease and cystic fibrosis.  Mixed saliva was collected under carefully standardised conditions and amylase was measured by the method of Dahlqvist.  There was a wide scatter of values in the 84 normal subjects, but concentrations rose from very low levels at birth to reach adult levels by the age of 6 months to 1 year. Salivary amylase activity rose normally over ten weeks in one premature infant fed milk by gastrostomy.  Thirteen children with coeliac disease and 9 children with cystic fibrosis mostly had normal salivary amylase concentrations.  Six out of 12 malnourished children with jejunal villous atrophy of uncertain aetiology had low levels which rose to normal as recovery began.'
    #print e.tokenize(s)
