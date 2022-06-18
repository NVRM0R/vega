import sys
from sys import path as sysPath
from os import path
import os
import nibabel as nb
import json
currentPath = os.path.abspath(os.getcwd())
sysPath.append('../cluster_roi')
import clustering as clustering




def workloadCalculateMatrix(projectPath,corrThresh,maskThresh):
    clustering.calculateMatrix("../vega/"+projectPath,corrThresh,maskThresh)
    
    jsonFile = path.join(projectPath,'info.json')
    with open(jsonFile, 'r') as file:
        data = json.load(file)
        data['status'] = 'ready'
        data['corrThresh'] = corrThresh
        data['maskThresh'] = maskThresh
        
    with open(jsonFile, 'w') as file:
        json.dump(data, file)
    return

def workloadParcellate(projectPath,k,maskThresh):
    print("maskThresh ",maskThresh," @ k=",k,file=sys.stderr)
    clustering.cluster("../vega/"+projectPath,k,maskThresh)
    jsonFile = path.join(projectPath,'info.json')
    with open(jsonFile, 'r') as file:
        data = json.load(file)
        data['status'] = 'ready'
        listOfParcs = data['parc']
        listOfParcs.append(str(k))
        data['parc'] = listOfParcs
    with open(jsonFile, 'w') as file:
        json.dump(data, file)
    return