
import sys
import os
from os import mkdir
from scipy.io import loadmat
from scipy.ndimage import zoom
import json
import nibabel as nb
def fitAnatomical(nii,coefs):
    nii = nb.as_closest_canonical(nii)
    niiData = nii.get_fdata()
    NewNiiData = zoom(niiData,coefs)
    NewNii = nb.Nifti1Image(NewNiiData,nii.affine)
    return NewNii


def newProject(projectName,file,connProject):
    folderPath = os.path.join("filePoint",projectName.split('.')[0])
    if not os.path.exists(folderPath):
        mkdir(folderPath,mode=0o777)
    connFile = open(os.path.join(folderPath,projectName),"wb")
    connFile.write(file)
    connFile.close()
    if(connProject=='true'):
        print("Loaded CONN project",file=sys.stderr)
        matData = loadmat(os.path.join(folderPath,projectName))['CONN_x']
        func = matData['Setup'][0][0][0][0]['functional'][0][0][0][0][0][0][0]
        anat = matData['Setup'][0][0][0][0]['rois']['files'][0][0][0][0][0][0][0][0][0][0][0]
    else:
        func = ''
        anat = ''
    data = {
        "name":projectName,
        "status":"new", # new, setup, calculating, ready, parcellating
        "parc":['Исходный снимок'],
        "editable":"no",
    }
    with open(os.path.join(folderPath,'info.json'), 'w') as fp:
        json.dump(data, fp)
    print({'func':func,'anat':anat},file=sys.stderr)
    return {'func':func,'anat':anat}

def saveFile(projectName,anatFile,funcFile):
    try:
        folderPath = os.path.join("filePoint",projectName.split('.')[0])
        aFile = open(os.path.join(folderPath,"anatomicalOrigin.nii"),"wb")
        aFile.write(anatFile)
        aFile.close()
        fFile = open(os.path.join(folderPath,"functional.nii"),"wb")
        fFile.write(funcFile)
        fFile.close()
        mask = nb.load(os.path.join(folderPath,"anatomicalOrigin.nii"))
        func = nb.load(os.path.join(folderPath,"functional.nii"))
        MaskS = mask.shape
        funcS = func.shape
        coefs = [funcS[0]/MaskS[0],funcS[1]/MaskS[1],funcS[2]/MaskS[2]]
        newMask = fitAnatomical(mask,coefs)
        fileMask = os.path.join(folderPath,"anatomical.nii")
        nb.save(newMask,fileMask)
        return True
    except Exception:
        return False

