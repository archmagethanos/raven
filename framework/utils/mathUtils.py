'''
 This file contains the mathematical methods used in the framework.
 Some of the methods were in the PostProcessor.py
 created on 03/26/2015
 @author: senrs
'''

from __future__ import division, print_function, unicode_literals, absolute_import
import warnings
warnings.simplefilter('default',DeprecationWarning)

import math
import copy
from scipy import interpolate
import numpy as np
from scipy.interpolate import Rbf, griddata

def normal(x,mu=0.0,sigma=1.0):
  """
    Computation of normal pdf
    @ In, x, list or np.array, x values
    @ In, mu, float, optional, mean
    @ In, sigma, float, optional, sigma
    @ Out, returnNormal, list or np.array, pdf
  """
  returnNormal = (1.0/(sigma*math.sqrt(2*math.pi)))*math.exp(-(x - mu)**2/(2.0*sigma**2))
  return returnNormal

def normalCdf(x,mu=0.0,sigma=1.0):
  """
    Computation of normal cdf
    @ In, x, list or np.array, x values
    @ In, mu, float, optional, mean
    @ In, sigma, float, optional, sigma
    @ Out, cdfReturn, list or np.array, cdf
  """
  cdfReturn = 0.5*(1.0+math.erf((x-mu)/(sigma*math.sqrt(2.0))))
  return cdfReturn

def skewNormal(x,alphafactor,xi,omega):
  """
    Computation of skewness normal
    @ In, x, list or np.array, x values
    @ In, alphafactor, float, the alpha factor (shape)
    @ In, xi, float, xi (location)
    @ In, omega, float, omega factor (scale)
    @ Out, returnSkew, float, skew
  """
  def phi(x): return (1.0/math.sqrt(2*math.pi))*math.exp(-(x**2)/2.0) #FIXME shouldn't this use normal() above?
  def Phi(x): return 0.5*(1+math.erf(x/math.sqrt(2))) #FIXME same, shouldn't this use the above?
  returnSkew = (2.0/omega)*phi((x-xi)/omega)*Phi(alphafactor*(x-xi)/omega)
  return returnSkew

def createInterp(x, y, lowFill, highFill, kind='linear'):
  """
    Simpson integration rule #FIXME this is not an accurate docstring, and I don't know what this method does
    @ In, x, list or np.array, x values
    @ In, y, list or np.array, y values
    @ In, lowFill, float, minimum interpolated value
    @ In, highFill, float, maximum interpolated value
    @ In, kind, string, optional, interpolation type (default=linear)
    @ Out, sumVar, float, integral #FIXME incorrect
  """
  interp = interpolate.interp1d(x, y, kind)
  low = x[0]
  def myInterp(x):
    try:
      return interp(x)+0.0
    except ValueError:
      if x <= low:
        return lowFill
      else:
        return highFill
  return myInterp

def simpson(f, a, b, n):
  """
    Simpson integration rule
    @ In, f, instance, the function to integrate
    @ In, a, float, lower bound
    @ In, b, float, upper bound
    @ In, n, int, number of integration steps
    @ Out, sumVar, float, integral
  """
  h = (b - a) / float(n)
  sumVar = f(a) + f(b)
  for i in range(1,n, 2):
    sumVar += 4*f(a + i*h)
  for i in range(2, n-1, 2):
    sumVar += 2*f(a + i*h)
  sumVar = sumVar * h / 3.0
  return sumVar

def getGraphs(functions, fZStats = False):
  """
    Returns the graphs of the functions.
    The functions are a list of (dataStats, cdf_function, pdf_function,name)
    It returns a dictionary with the graphs and other statistics calculated.
    @ In, functions, list, list of functions (data_stats_dict, cdf_function, pdf_function,name)
    @ In, fZStats, bool, optional, true if the F(z) (cdf) needs to be computed
    @ Out, retDict, dict, the return dictionary
  """
  retDict = {}
  dataStats = [x[0] for x in functions]
  means = [x["mean"] for x in dataStats]
  stddevs = [x["stdev"] for x in dataStats]
  cdfs = [x[1] for x in functions]
  pdfs = [x[2] for x in functions]
  names = [x[3] for x in functions]
  low = min([m - 3.0*s for m,s in zip(means,stddevs)])
  high = max([m + 3.0*s for m,s in zip(means,stddevs)])
  lowLow = min([m - 5.0*s for m,s in zip(means,stddevs)])
  highHigh = max([m + 5.0*s for m,s in zip(means,stddevs)])
  minBinSize = min([x["minBinSize"] for x in dataStats])
  print("Graph from ",low,"to",high)
  n = int(math.ceil((high-low)/minBinSize))
  interval = (high - low)/n

  #Print the cdfs and pdfs of the data to be compared.
  origCdfAndPdfArray = []
  origCdfAndPdfArray.append(["x"])
  for name in names:
    origCdfAndPdfArray.append([name+'_cdf'])
    origCdfAndPdfArray.append([name+'_pdf'])

  for i in range(n):
    x = low+interval*i
    origCdfAndPdfArray[0].append(x)
    k = 1
    for stats, cdf, pdf, name in functions:
      origCdfAndPdfArray[k].append(cdf(x))
      origCdfAndPdfArray[k+1].append(pdf(x))
      k += 2
  retDict["cdf_and_pdf_arrays"] = origCdfAndPdfArray

  def fZ(z):
    """
      Compute f(z) with a simpson rule
      @ In, z, float, the coordinate
      @ Out, fZ, the f(z)
    """
    return simpson(lambda x: pdfs[0](x)*pdfs[1](x-z), lowLow, highHigh, 1000)

  if len(means) < 2:
    return
  midZ = means[0]-means[1]
  lowZ = midZ - 3.0*max(stddevs[0],stddevs[1])
  highZ = midZ + 3.0*max(stddevs[0],stddevs[1])

  #print the difference function table.
  fZTable = [["z"],["f_z(z)"]]
  zN = 20
  intervalZ = (highZ - lowZ)/zN
  for i in range(zN):
    z = lowZ + intervalZ*i
    fZTable[0].append(z)
    fZTable[1].append(fZ(z))
  cdfAreaDifference = simpson(lambda x:abs(cdfs[1](x)-cdfs[0](x)),lowLow,highHigh,100000)
  retDict["f_z_table"] = fZTable

  def firstMomentSimpson(f, a, b, n):
    """
      Compute the first simpson method
      @ In, f, method, the function f(x)
      @ In, a, float, lower bound
      @ In, b, float, upper bound
      @ In, n, int, the number of discretizations
      @ Out, firstMomentSimpson, float, the moment
    """
    return simpson(lambda x:x*f(x), a, b, n)

  #print a bunch of comparison statistics
  pdfCommonArea = simpson(lambda x:min(pdfs[0](x),pdfs[1](x)),
                            lowLow,highHigh,100000)
  for i in range(len(pdfs)):
    pdfArea = simpson(pdfs[i],lowLow,highHigh,100000)
    retDict['pdf_area_'+names[i]] = pdfArea
    dataStats[i]["pdf_area"] = pdfArea
  retDict['cdf_area_difference'] = cdfAreaDifference
  retDict['pdf_common_area'] = pdfCommonArea
  dataStats[0]["cdf_area_difference"] = cdfAreaDifference
  dataStats[0]["pdf_common_area"] = pdfCommonArea
  if fZStats:
    sumFunctionDiff = simpson(fZ, lowZ, highZ, 1000)
    firstMomentFunctionDiff = firstMomentSimpson(fZ, lowZ,highZ, 1000)
    varianceFunctionDiff = simpson(lambda x:((x-firstMomentFunctionDiff)**2)*fZ(x),lowZ,highZ, 1000)
    retDict['sum_function_diff'] = sumFunctionDiff
    retDict['first_moment_function_diff'] = firstMomentFunctionDiff
    retDict['variance_function_diff'] = varianceFunctionDiff
  return retDict


def countBins(sortedData, binBoundaries):
  """
    This method counts the number of data items in the sorted_data
    Returns an array with the number.  ret[0] is the number of data
    points <= binBoundaries[0], ret[len(binBoundaries)] is the number
    of points > binBoundaries[len(binBoundaries)-1]
    @ In, sortedData, list or np.array,the data to be analyzed
    @ In, binBoundaries, list or np.array, the bin boundaries
    @ Out, ret, list, the list containing the number of bins
  """
  binIndex = 0
  sortedIndex = 0
  ret = [0]*(len(binBoundaries)+1)
  while sortedIndex < len(sortedData):
    while not binIndex >= len(binBoundaries) and \
          sortedData[sortedIndex] > binBoundaries[binIndex]:
      binIndex += 1
    ret[binIndex] += 1
    sortedIndex += 1
  return ret

def log2(x):
  """
   Compute log2
   @ In, x, float, the coordinate x
   @ Out, logTwo, float, log2
  """
  logTwo = math.log(x)/math.log(2.0)
  return logTwo

def calculateStats(data):
  """
    Calculate statistics on a numeric array data
    and return them in a dictionary
    @ In, data, list or numpy.array, the data
    @ Out, ret, dict, the dictionary containing the stats
  """

  sum1 = 0.0
  sum2 = 0.0
  n = len(data)
  for value in data:
    sum1 += value
    sum2 += value**2

  mean = sum1/n
  variance = (1.0/n)*sum2-mean**2
  sampleVariance = (n/(n-1.0))*variance
  stdev = math.sqrt(sampleVariance)

  m4 = 0.0
  m3 = 0.0
  for value in data:
    m3 += (value - mean)**3
    m4 += (value - mean)**4
  m3 = m3/n
  m4 = m4/n
  skewness = m3/(variance**(3.0/2.0))
  kurtosis = m4/variance**2 - 3.0

  ret = {}
  ret["mean"] = mean
  ret["variance"] = variance
  ret["sampleVariance"] = sampleVariance
  ret["stdev"] = stdev
  ret["skewness"] = skewness
  ret["kurtosis"] = kurtosis
  return ret

def historySetWindow(vars,numberOfTimeStep):
  """
    Method do to compute
    @ In, vars, HistorySet, is an historySet
    @ In, numberOfTimeStep, int, number of time samples of each history
    @ Out, outDic, dict, it contains the temporal slice of all histories
  """

  outKeys = vars.getParaKeys('outputs')
  inpKeys = vars.getParaKeys('inputs')

  outDic = []

  for t in range(numberOfTimeStep):
    newVars={}
    for key in inpKeys+outKeys:
      newVars[key]=np.zeros(0)

    hs = vars.getParametersValues('outputs')
    for history in hs:
      for key in inpKeys:
        newVars[key] = np.append(newVars[key],vars.getParametersValues('inputs')[history][key])

      for key in outKeys:
        newVars[key] = np.append(newVars[key],vars.getParametersValues('outputs')[history][key][t])

    outDic.append(newVars)

  return outDic

#
# I need to convert it in multi-dimensional
# Not a priority yet. Andrea
#
# def computeConcaveHull(coordinates,alphafactor):
#   """
#    Method to compute the Concave Hull of a cloud of points
#    @ In, coordinates, matrix-like, (M,N) -> M = number of coordinates, N, number of dimensions
#    @ In, alphafactorfactor, float, shape factor tollerance to influence the gooeyness of the border.
#   """
#   def add_edge(edges, edge_points, coords, i, j):
#     """
#     Add a line between the i-th and j-th points,
#     if not in the list already
#     """
#     if (i, j) in edges or (j, i) in edges: return
#     edges.add( (i, j) )
#     edge_points.append(coords[ [i, j] ])
#
#   #coords = np.array([point.coords[0] for point in points])
#
#   tri = Delaunay(coordinates)
#   edges = set()
#   edge_points = []
#   # loop over triangles:
#   # ia, ib, ic = indices of corner points of the
#   # triangle
#   for ia, ib, ic in tri.simplices:
#     pa = coordinates[ia]
#     pb = coordinates[ib]
#     pc = coordinates[ic]
#
#     # Lengths of sides of triangle
#     a = math.sqrt((pa[0]-pb[0])**2 + (pa[1]-pb[1])**2)
#     b = math.sqrt((pb[0]-pc[0])**2 + (pb[1]-pc[1])**2)
#     c = math.sqrt((pc[0]-pa[0])**2 + (pc[1]-pa[1])**2)
#
#     # Semiperimeter of triangle
#     s = (a + b + c)/2.0
#
#     # Area of triangle by Heron's formula
#     area = math.sqrt(s*(s-a)*(s-b)*(s-c))
#     circum_r = a*b*c/(4.0*area)
#
#     # Here's the radius filter.
#     #print circum_r
#     if circum_r < 1.0/alphafactor:
#       add_edge(edges, edge_points, coordinates, ia, ib)
#       add_edge(edges, edge_points, coordinates, ib, ic)
#       add_edge(edges, edge_points, coordinates, ic, ia)
#
#   m = geometry.MultiLineString(edge_points)
#   triangles = list(polygonize(m))
#   return cascaded_union(triangles), edge_points

def convertNumpyToLists(inputDict):
  """
    Method aimed to convert a dictionary containing numpy
    arrays or a single numpy array in list
    @ In, inputDict, dict or numpy array,  object whose content needs to be converted
    @ Out, response, dict or list, same object with its content converted
  """
  returnDict = inputDict
  if type(inputDict) == dict:
    for key, value in inputDict.items():
      if   type(value) == np.ndarray: returnDict[key] = value.tolist()
      elif type(value) == dict      : returnDict[key] = (convertNumpyToLists(value))
      else                          : returnDict[key] = value
  elif type(inputDict) == np.ndarray: returnDict = inputDict.tolist()
  return returnDict

def interpolateFunction(x,y,option,z = None,returnCoordinate=False):
  """
    Method to interpolate 2D/3D points
    @ In, x, ndarray or cached_ndarray, the array of x coordinates
    @ In, y, ndarray or cached_ndarray, the array of y coordinates
    @ In, z, ndarray or cached_ndarray, optional, the array of z coordinates
    @ In, returnCoordinate, bool, optional, true if the new coordinates need to be returned
    @ Out, i, ndarray or cached_ndarray or tuple, the interpolated values
  """
  options = copy.copy(option)
  if x.size <= 2: xi = x
  else          : xi = np.linspace(x.min(),x.max(),int(options['interpPointsX']))
  if z != None:
    if y.size <= 2: yi = y
    else          : yi = np.linspace(y.min(),y.max(),int(options['interpPointsY']))
    xig, yig = np.meshgrid(xi, yi)
    try:
      if ['nearest','linear','cubic'].count(options['interpolationType']) > 0 or z.size <= 3:
        if options['interpolationType'] != 'nearest' and z.size > 3: zi = griddata((x,y), z, (xi[None,:], yi[:,None]), method=options['interpolationType'])
        else: zi = griddata((x,y), z, (xi[None,:], yi[:,None]), method='nearest')
      else:
        rbf = Rbf(x,y,z,function=str(str(options['interpolationType']).replace('Rbf', '')), epsilon=int(options.pop('epsilon',2)), smooth=float(options.pop('smooth',0.0)))
        zi  = rbf(xig, yig)
    except Exception as ae:
      if 'interpolationTypeBackUp' in options.keys():
        print(UreturnPrintTag('UTILITIES')+': ' +UreturnPrintPostTag('Warning') + '->   The interpolation process failed with error : ' + str(ae) + '.The STREAM MANAGER will try to use the BackUp interpolation type '+ options['interpolationTypeBackUp'])
        options['interpolationTypeBackUp'] = options.pop('interpolationTypeBackUp')
        zi = interpolateFunction(x,y,z,options)
      else: raise Exception(UreturnPrintTag('UTILITIES')+': ' +UreturnPrintPostTag('ERROR') + '-> Interpolation failed with error: ' +  str(ae))
    if returnCoordinate: return xig,yig,zi
    else               : return zi
  else:
    try:
      if ['nearest','linear','cubic'].count(options['interpolationType']) > 0 or y.size <= 3:
        if options['interpolationType'] != 'nearest' and y.size > 3: yi = griddata((x), y, (xi[:]), method=options['interpolationType'])
        else: yi = griddata((x), y, (xi[:]), method='nearest')
      else:
        xig, yig = np.meshgrid(xi, yi)
        rbf = Rbf(x, y,function=str(str(options['interpolationType']).replace('Rbf', '')),epsilon=int(options.pop('epsilon',2)), smooth=float(options.pop('smooth',0.0)))
        yi  = rbf(xi)
    except Exception as ae:
      if 'interpolationTypeBackUp' in options.keys():
        print(UreturnPrintTag('UTILITIES')+': ' +UreturnPrintPostTag('Warning') + '->   The interpolation process failed with error : ' + str(ae) + '.The STREAM MANAGER will try to use the BackUp interpolation type '+ options['interpolationTypeBackUp'])
        options['interpolationTypeBackUp'] = options.pop('interpolationTypeBackUp')
        yi = interpolateFunction(x,y,options)
      else: raise Exception(UreturnPrintTag('UTILITIES')+': ' +UreturnPrintPostTag('ERROR') + '-> Interpolation failed with error: ' +  str(ae))
    if returnCoordinate: return xi,yi
    else               : return yi

def numpyNearestMatch(findIn,val):
  """
    Given an array, find the entry that most nearly matches the given value.
    @ In, findIn, np.array, the array to look in
    @ In, val, float or other compatible type, the value for which to find a match
    @ Out, returnMatch, tuple, index where match is and the match itself
  """
  idx = (np.abs(findIn-val)).argmin()
  returnMatch = idx,findIn[idx]
  return returnMatch

def NDInArray(findIn,val,tol=1e-12):
  """
    checks a numpy array of numpy arrays for a near match, then returns info.
    @ In, findIn, np.array, numpy array of numpy arrays (both arrays can be any length)
    @ In, val, tuple/list/numpy array, entry to look for in findIn
    @ In, tol, float, optional, tolerance to check match within
    @ Out, (bool,idx,looking) -> (found/not found, index where found or None, findIn entry or None)
  """
  if len(findIn)<1:
    return False,None,None
  targ = []
  found = False
  for idx,looking in enumerate(findIn):
    num = looking - val
    den = np.array(val)
    #div 0 error
    for i,v in enumerate(den):
      if v == 0.0:
        if looking[i] != 0:
          den[i] = looking[i]
        elif looking[i] + den[i] != 0.0:
          den[i] = 0.5*(looking[i] + den[i])
        else:
          den[i] = 1
    if np.all(abs(num / den)<tol):
      found = True
      break
  if not found:
    return False,None,None
  return found,idx,looking

