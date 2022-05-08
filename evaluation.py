import sys
from sys import path
import os
import nibabel as nb
currentPath = os.path.abspath(os.getcwd())
path.append('../cluster_roi')
import clustering as clustering




def workloadCalculateMatrix(projectPath):
    clustering.calculateMatrix("../vega/"+projectPath)
    
    jsonFile = path.join(projectPath,'info.json')
    with open(jsonFile, 'r') as file:
        data = json.load(file)
        data['status'] = 'ready'
    with open(jsonFile, 'w') as file:
        json.dump(data, file)
    return

def workloadParcellate(projectPath,k):
    clustering.cluster("../vega/"+projectPath,k)
    
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