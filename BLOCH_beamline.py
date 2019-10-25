print("---- BLOCH beamline ----")
print("\tLast updated 02.13.2018 \n")
print("\tLatest change: Simple resolution calculators\n")

import h5py
import numpy as np
from pylab import *

# Use the path library to avoid problems with windows vs mac/linux slashes in paths
from pathlib import Path

#*************************************************************************************
#*************************************************************************************

#  Functions for loading calculation outputs from SPECTRA

#*************************************************************************************
#*************************************************************************************

#*****************************************************
def loadSPECTRACalc(fileToOpen):
#*****************************************************  
	"""
		Load a 'partial flux' vs energy spectrum
		Returns type: dictionary containing 'mono_energy' and 'flux' lists
	"""
	firstDataLine = 11  # This works because the output files always have the same sized header
	dataDict={'mono_energy':[],'flux':[]}

	with open(fileToOpen,'r') as fp:

		for lineNumber,line in enumerate(fp):
			if lineNumber >= firstDataLine:
				data=line.rstrip('\n').split(' ')

				# Data columns are usually separated by a double space, but if an element is negative
				# then the minus sign eats one of the spaces. This is a bit of a hack workaround - split by a single ' '
				# (which gives an additional empty element when things are double spaced) then delete any empty elements
				for index,datapoint in enumerate(data):
					if datapoint=='':	del data[index]

				if len(data)>0:
					dataDict['mono_energy'].append(float(data[0]))
					dataDict['flux'].append(float(data[1]))

	return dataDict


#*****************************************************
def loadSPECTRA_image(fileToOpen):
#*****************************************************  
	"""
		Load a spatial (x,y) flux map calculated at a fixed energy 
		Returns type: 2d numpy array, 4 element list consisting of [x start, x stop, y start, y stop]
	"""

	firstDataLine = 11
	fp = open(fileToOpen,'r')
	lineCounter=0
	dataDict={'x':[],'y':[],'flux':[]}
	for line in fp:
		lineCounter=lineCounter+1
		if lineCounter >= firstDataLine:
			data=line.rstrip('\n').split()
			if len(data)>0:
				dataDict['flux'].append(float(data[2]))
				dataDict['x'].append(float(data[0]))
				dataDict['y'].append(float(data[1]))
	fp.close()
	
	ySize=1
	previousElement=dataDict['y'][0]
	for index,element in enumerate(dataDict['y']):
		if element != previousElement:
			ySize = int(index)
			break
	xSize = int(len(dataDict['y'])/ySize)
	loadedImage=np.zeros((xSize,ySize))

	for ii in range(xSize):
		for jj in range(ySize):
			loadedImage[ii][jj] = dataDict['flux'][jj + (ii*ySize)]

	imageExtent = [dataDict['x'][0],dataDict['x'][ySize-1],dataDict['y'][0],dataDict['y'][-1]]
	return loadedImage,imageExtent


#*************************************************************************************
#*************************************************************************************
#
#  Functions for loading HDF5 data from motorscanGUI
#
# HDF5 files contain a number of *scans*. Each *scan* consists of a number of *datasets*
# For example, if you performed a sweep of the mono energy while recording the diode current 
# and mirror temperature, that would be one *scan* containing two *datasets*.
#*************************************************************************************
#*************************************************************************************

#*************************************
def loadHDF5(path):
#*************************************
	"""
		Load an HDF5 file into memory. 
		Return type: h5py._hl.files.File
	"""
	h5_fp = h5py.File(str(path), 'r')
	try:
		h5_fp = h5py.File(str(path), 'r')
	except:
		print("Couldn't load that file. Is the path correct?\n\t'{0}'".format(path))
		return 0

	return h5_fp

#*************************************
def HDF5info(path):
#*************************************  
	"""
		Given a path to an HDF5 file, print information about the 
		scans it contains
		Return type: none
	"""
	h5_fp=loadHDF5(path)

	if h5_fp !=0:
		print("\n{0} contains {1} scans:\n(I am stripping off the 'entry' part of their name)\n".format(path,len(h5_fp)))
		print("\nScan index\t # datasets \t # points in first dataset")
		print("----------------------------------------------------------")
		scanNames = [key.lstrip('entry') for key in h5_fp.keys()]
		for scanName in scanNames:
			dataSetNames = [key for key in h5_fp["entry{0}/measurement".format(scanName)].keys()]
			dataSetLength = len(np.array(h5_fp["entry{0}/measurement/{1}".format(scanName,dataSetNames[0])]))
			print("{0}\t\t{1}\t\t{2}".format(scanName,len(dataSetNames),dataSetLength));
		
		h5_fp.close()

#*******************************************
def HDF5scaninfo(path,scanIndex):
#*******************************************
	"""
		Given a path to an HDF5 file and the *number* of a scan
		print the names of all datasets in that scan
		Return type: none
	"""
	h5_fp=loadHDF5(path)
	
	try:
		dataSetNames = [key for key in h5_fp["entry{0}/measurement".format(scanIndex)].keys()]

	except:
		print("Couldn't find the dataset names.\n\tDoes 'entry{0}' exist in this hdf5 file?".format(scanIndex))
		print("\tFind out by running HDF5info(path='{0}')".format(path))
		return

	print("entry{0} contains {1} datasets:\n".format(scanIndex,len(dataSetNames)))
	for dataSetName in dataSetNames:
		print("\t",dataSetName)

	h5_fp.close()

#*******************************************
def HDF5getScanList(path):
#*******************************************
	"""
		Given a path to an HDF5 file, return a list of all the scan names it contains
		Return type: list
	"""

	h5_fp=loadHDF5(path)

	scanNames = [key.lstrip('entry') for key in h5_fp.keys()]

	h5_fp.close()

	return scanNames

#*************************************
def HDF5loadscan(path,scanIndex):
#*************************************
	"""
		Given a path to an HDF5 file and the *number* of a scan
		(assuming all scans are named "entryX"), load all datasets in that scan
		Return type: dictionary  
	"""
	h5_fp=loadHDF5(path)

	try:
		dataSetNames = [key for key in h5_fp["entry{0}/measurement".format(scanIndex)].keys()]

	except:
		print("Couldn't find the dataset names.\n\tDoes 'entry{0}' exist in this hdf5 file?".format(scanIndex))
		print("\tFind out by running HDF5info(path='{0}')".format(path))
		return
		
	dataDict = {}
	
	for name in dataSetNames:
		dataDict[name]=np.array(h5_fp["entry{0}/measurement/{1}".format(scanIndex,name)])

	h5_fp.close()

	return dataDict

#******************************
def getGratingAngle(hv,lineDensity,cff):
#******************************
	"""
		For the PGM, calculate the grating pitch. Formula is copied blindly from Mat's spreadsheet,
		because I have complete faith in him.  
	"""    
	h = 6.62607e-34
	c = 2.99792e8
	joules_per_eV = 1.60218e-19
	
	wavelength = h*c/(hv*joules_per_eV)
	
	alpha = math.acos(wavelength*lineDensity/(cff**2 -1) * (math.sqrt(cff**2 + (cff**2-1)**2/(wavelength**2*lineDensity**2))-1 ))
	# in radians!
	
	beta = np.rad2deg(math.asin(cff*math.sin(alpha)))
	return beta

#******************************
def calibrateMonoEnergy(monoEnergy):
#******************************
	"""
		Given a list of photon energies, apply an empirically determined calibration correction
		Return type: list of corrected energies  
	"""
	print("Implementing mono calibration according to Mats, May 2018")
	return monoEnergy-0.026 + monoEnergy*0.0185

#******************************
def calculateMonoAcceptance(hgap,vgap):
#******************************
	sigma = 0.15e-3    # Beam sigma in radians
	M1_distance = 14   #distance in meters from the source
	hgap_offset = 3
	vgap_offset = 3.5
	hgap_true = hgap - hgap_offset
	vgap_true = vgap - vgap_offset
	h_acceptance= (hgap_true/1000) / ( 2*M1_distance*tan(sigma/2))
	v_acceptance= (vgap_true/1000) / ( 2*M1_distance*tan(sigma/2))
	print("Mono horizontal gap size of {0} is {1} after accounting for offset.\nThis means an acceptance of {2:1.3f} sigma".format(hgap,hgap_true,h_acceptance))
	print("Mono vertical gap size of {0} is {1} after accounting for offset.\nThis means an acceptance of {2:1.3f} sigma".format(vgap,vgap_true,v_acceptance))

#******************************
def calculateFrontEndAcceptance(opening):
#******************************
	sigma = 0.15e-3    # Beam sigma in radians
	FE_distance = (7.162+7.822)/2   #distance in meters from the source
	acceptance= (opening/1000) / ( 2*FE_distance*tan(sigma/2))
	print("A centered moveable mask aperture size of {} means an acceptance of {:1.3f} sigma".format(opening,acceptance))


# Assume cff 2.25, 800l/mm
# returns slit-limited resolution in meV
def beamLineResolution(input_hv,exitslit_um):

    #I got these values from digitizing Mat's printout
    resolution_100umSlits=[0.47,1.33,2.5,3.68,7.12,10.95,15.43,28.48,43.93,80.6,124]
    hv=[10,20,30,40,60,80,100,150,200,300,400]


    for index,element in enumerate(hv):
        if np.float(input_hv)<=np.float(element):
            closestUnder_index=index-1
            closestOver_index=index
            terminatedOK = True
            break

    if terminatedOK == True:

        hv0 = hv[closestUnder_index]
        
        res0 = resolution_100umSlits[closestUnder_index]*(exitslit_um/100)
        hv1 = hv[closestOver_index]
        res1 = resolution_100umSlits[closestOver_index]*(exitslit_um/100)   
        res0_weight = abs((hv1-input_hv))/(hv1-hv0)
        res1_weight = abs((hv0-input_hv))/(hv1-hv0)
        return float(res0*res0_weight + res1*res1_weight)

    else:
        return float('NaN')

# in meV
def analyzerResolution(passEnergy_eV,slit_mm):
	hemisphereRadius = 200
	return 1000*passEnergy_eV*slit_mm/((2*hemisphereRadius))



#*******************************************    
def lookupM1Pitch(lookupTable,hv):
#*******************************************   
	try: fp=open(lookupTable,'r')
	except:
		print("Couldn't find a lookup table named",lookupTable)
		return 0
	next(fp)

	pitch=[]
	for line in fp:
		data=(line.rstrip('\n').split('\t'))
		pitch.append([float(data[0]),float(data[1])])
	fp.close()    
	
	terminatedOK = False
	
	for index,element in enumerate(pitch):
		if index==0 and element[0]==hv:
			closestUnder=pitch[index]
			closestOver=pitch[index+1]
			terminatedOK = True
			break
		if index==0 and element[0]>hv:
			terminatedOK = False
			break            
		if index>0 and element[0]>=hv:
			closestUnder=pitch[index-1]
			closestOver=pitch[index]
			terminatedOK = True
			break

	if terminatedOK == True:

		hv0 = closestUnder[0]
		pitch0 = closestUnder[1]
		hv1 = closestOver[0]
		pitch1 = closestOver[1]   
		pitch0_weight = abs((hv1-hv))/(hv1-hv0)
		pitch1_weight = abs((hv0-hv))/(hv1-hv0)
		output = pitch0*pitch0_weight + pitch1*pitch1_weight

	if terminatedOK == False:
		print("ERROR: requested photon energy",hv,"is not within the lookup table (10 .. 800eV)")
		return float('NaN')
	
	return output

	
#*******************************************    
def lookupHarmonicEnergy(lookupTable,gap,orderNumber):
#*******************************************   
	try: fp=open(lookupTable,'r')
	except:
		print("Couldn't find the lookup table")
		return 0
	next(fp)
	next(fp)
	harmonic=[]
	for line in fp:
		data=(line.rstrip('\n').split('\t'))
		harmonic.append([float(data[0]),float(data[1])])
	fp.close()    
	
	terminatedOK = False
	
	for index,element in enumerate(harmonic):
		if index==0 and element[0]==gap:
			closestUnder=harmonic[index]
			closestOver=harmonic[index+1]
			terminatedOK = True
			break
		if index==0 and element[0]>gap:
			terminatedOK = False
			break            
		if index>0 and element[0]>=gap:
			closestUnder=harmonic[index-1]
			closestOver=harmonic[index]
			terminatedOK = True
			break

	if terminatedOK == True:

		gap0 = closestUnder[0]
		hv0 = closestUnder[1]
		gap1 = closestOver[0]
		hv1 = closestOver[1]   
		hv0_weight = abs((gap1-gap))/(gap1-gap0)
		hv1_weight = abs((gap0-gap))/(gap1-gap0)
		output = hv0*hv0_weight + hv1*hv1_weight

	if terminatedOK == False:
		print("ERROR: requested gap",gap,"is not within the lookup table")
		return float('NaN')
	
	if orderNumber == 1: return output
	elif orderNumber == 2: return 1.956*output
	elif orderNumber == 3: return 2.75*output   
	else:
		print("I don't know the multiplier for harmonics of order",harmonicOrder)
		return float('NaN') 

	
#*******************************************    
def lookupGap(lookupTable,hv):
#*******************************************   
	try: fp=open(lookupTable,'r')
	except:
		print("Couldn't find the lookup table")
		return 0
	next(fp)
	next(fp)
	harmonic=[]
	for line in fp:
		data=(line.rstrip('\n').split('\t'))
		harmonic.append([float(data[1]),float(data[0])])
	fp.close()    
	
	terminatedOK = False
	
	for index,element in enumerate(harmonic):
		if index==0 and element[0]==hv:
			closestUnder=harmonic[index]
			closestOver=harmonic[index+1]
			terminatedOK = True
			break
		if index==0 and element[0]>hv:
			terminatedOK = False
			break            
		if index>0 and element[0]>=hv:
			closestUnder=harmonic[index-1]
			closestOver=harmonic[index]
			terminatedOK = True
			break

	if terminatedOK == True:

		hv0 = closestUnder[0]
		gap0 = closestUnder[1]
		hv1 = closestOver[0]
		gap1 = closestOver[1]   
		gap0_weight = abs((hv1-hv))/(hv1-hv0)
		gap1_weight = abs((hv0-hv))/(hv1-hv0)
		output = gap0*gap0_weight + gap1*gap1_weight

	if terminatedOK == False:
		print("ERROR: requested hv",hv,"is not within the lookup table (10.8 .. 230eV)")
		return float('NaN')
	
	return output

	
#******************************
def currentToFlux(current,hv):
#******************************
	"""

	"""
	electronsPerCoulomb = float('6.2415e18')
	return current* electronsPerCoulomb / diodeResponse(hv)



#******************************
def fluxToCurrent(flux,hv):
#******************************
	"""

	"""
	electronsPerCoulomb = float('6.2415e18')
	return flux*diodeResponse(hv) / electronsPerCoulomb

#*******************************************    
def diodeResponse(hv):
#*******************************************   
	"""
	"""

	lookupTable = Path('LookupTables/AUX100_quantum_efficiency.txt')
	try:
		fp=open(lookupTable,'r')
	except:
		print("Couldn't find the lookup table (AUX100_quantum_efficiency.txt)")
		return 0
	next(fp)
	QE=[]
	for line in fp:
		data=(line.rstrip('\n').split('\t'))
		QE.append([float(data[0]),float(data[1])])
	fp.close()    
	
	terminatedOK = False

	for index,element in enumerate(QE):
		if element[0]<hv:
			closestUnder=QE[index]
			closestOver=QE[index-1]
			terminatedOK = True
			break

	if terminatedOK == True:

		hv0 = closestUnder[0]
		QE0 = closestUnder[1]
		hv1 = closestOver[0]
		QE1 = closestOver[1]   
		QE0_weight = abs((hv1-hv))/(hv1-hv0)
		QE1_weight = abs((hv0-hv))/(hv1-hv0)
		return float(QE0*QE0_weight + QE1*QE1_weight)

	else:
		print("ERROR: requested energy",hv,"is not within the lookup table (1.13 .. 1240eV)")
		return float('NaN')