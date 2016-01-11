#!/usr/bin/env python
#coding: utf-8

from __future__ import division

def calculateMAP(recallPoints):
    """
    Calculate and returns the Mean Average Precision out of the recall points.
    Works with either interpolated or not points.

    If the recall points list is empty returns 0.0.

    param recallPoints: list of tuples (precision, recall).
    return: a number, representing the MAP value.
    """
    N = len(recallPoints)
    pSum = sum([p for p, r in recallPoints])
    try:
        result = pSum / N
    except ZeroDivisionError:
        result = 0.0

    return result

def getAverageRecallPoints(recallPointsLst):
    """
    Get the average of the precision points across all the lists of recall
    points in the recallPointsLst param.

    param recallPointsLst: a list of lists of recall points:
    return a list with the average of the points in the param recallPointsLst.
    """
    average = [(0, r/100) for r in range(0, 101, 10)]
    for recallPoints in recallPointsLst:
        for iii, pair in enumerate(recallPoints):
            precision, recall = pair
            precision += average[iii][0]
            average[iii] = (precision, recall)
    amt = len(recallPointsLst)
    average = [(p/amt, r) for p, r in average]
    return average

def getRecallPointsAndPrecisionAt(relevants, results, point=10):
    """
    Calculate the recall points based on the list of known relevants, and a
    list of results, while also calculating the precision at point.

    Precision and recall values belong in the interval [0, 1].

    param relevants: a list with ids of documents representing the ground truth
    of relevants.
    param results: a list of ids of documents returned by a query.
    param point: the point to calculate the precision at (P@K) value.
    return: a tuple (list, number), where the list is the non interpolated
    recall points list, the points are (precision, recall). The number is the
    value of the precision at the point param point.
    """
    recallPoints = []
    relevants = set(relevants) # place relevants in a set for faster lookup
    N = len(relevants)
    relevantDocs = 0
    pAtPoint = 0

    for iii, docId in enumerate(results):
        if docId in relevants:
            relevantDocs += 1
            precision = relevantDocs / (iii + 1)
            try:
                recall = relevantDocs / N
            except ZeroDivisionError:
                raise ValueError("The list of relevants can't be empty")
            recallPoints.append((precision, recall))
        if iii == (point - 1) or (iii == len(results) - 1 and len(results) < point):
            pAtPoint = relevantDocs / point

    return recallPoints, pAtPoint

def interpolateRecallPoints(recallPoints):
    """
    Get a list of interpolated precision and recall. I.e., transforms the list
    of recall points in a list of recall points with 11 points.

    Does't change the recallPoints list.

    param recallPoints: a list of recall points in pairs (precision, recall),
    the values should belong in the interval [0, 1].
    return: a list with 11 pairs (precision,  recall) of interpolated recall
    points, in the interval [0, 1].
    """
    nRecallPoints = []
    if recallPoints:
        for rPoint in range(0, 101, 10):
            nRecall = rPoint / 100
            try:
                nPrecision = max([p for p, r in recallPoints if nRecall <= r])
            except ValueError:
                for rPoint in range(rPoint, 101,10):
                    nRecall = rPoint / 100
                    nRecallPoints.append((0.0, nRecall))
                break
            nRecallPoints.append((nPrecision, nRecall))
    return nRecallPoints

if __name__ == '__main__':
    # slides IR Baeza-Yates & Ribeiro-Neto
    recallPointsLst = []

    recallPoints = [(0.33, 0.33), (0.25, 0.66), (0.2, 1.0)]
    result = interpolateRecallPoints(recallPoints)
    assert result == [(0.33, 0.0), (0.33, 0.1), (0.33, 0.2), (0.33, 0.3), (0.25, 0.4), (0.25, 0.5), (0.25, 0.6), (0.2, 0.7), (0.2, 0.8), (0.2, 0.9), (0.2, 1.0)]
    recallPointsLst.append(result)

    recallPoints = [(1.0, 0.1), (0.66, 0.2), (0.5, 0.3), (0.4, 0.4), (0.33, 0.5)]
    result = interpolateRecallPoints(recallPoints)
    assert result == [(1.0, 0), (1.0, 0.1), (0.66, 0.2), (0.5, 0.3), (0.4, 0.4), (0.33, 0.5), (0.0, 0.6), (0.0, 0.7), (0.0, 0.8), (0.0, 0.9), (0.0, 1.0)]
    recallPointsLst.append(result)

    # no assertions because of the floating points
    result = averageRecallPoints(recallPointsLst)
    print("calculated average: {}".format(result))
    print("expected result: {}".format([(0.66, 0), (0.66, 0.1), (0.49, 0.2), (0.41, 0.3), (0.32, 0.4), (0.29, 0.5), (0.12, 0.6), (0.1, 0.7), (0.1, 0.8), (0.1, 0.9), (0.1, 1.0)]))

    print("everything worked!!!")
