#/usr/bin/python3
from crypt import methods
import base64
from curses.ascii import FS
import json
from logging import exception
from sre_constants import SUCCESS
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS, cross_origin
from scipy.io import loadmat
from threading import Thread

from os import listdir,mkdir,path,rmdir,remove
import glob
from os.path import exists
import sys
sys.path.append(path.join(sys.path[0], '../cluster_roi'))
import clustering as clustering

app = Flask('__name__')
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

def getProjects():
    result = listdir("filePoint/")
    return result
def loadProject(projectName):
    folderPath = path.join("filePoint",projectName)
    f = open(path.join(folderPath,"anatomical.nii"),"rb")
    anatomical=f.read(-1)
    f.close()
    anatomicalB64 = base64.b64encode(anatomical).decode('utf-8')
    return anatomicalB64

def newProject(projectName,file,connProject):
    folderPath = path.join("filePoint",projectName.split('.')[0])
    if not path.exists(folderPath):
        mkdir(folderPath,mode=0o777)
    connFile = open(path.join(folderPath,projectName),"wb")
    connFile.write(file)
    connFile.close()
    if(connProject=='true'):
        print("Loaded CONN project",file=sys.stderr)
        matData = loadmat(path.join(folderPath,projectName))['CONN_x']
        func = matData['Setup'][0][0][0][0]['functional'][0][0][0][0][0][0][0]
        anat = matData['Setup'][0][0][0][0]['rois']['files'][0][0][0][0][0][0][0][0][0][0][0]
    else:
        func = ''
        anat = ''
    data = {
        "name":projectName,
        "status":"new", # new,calculating,ready, parcellating
        "parc":['Исходный снимок'],
        "editable":"no",
    }
    with open(path.join(folderPath,'info.json'), 'w') as fp:
        json.dump(data, fp)
    print({'func':func,'anat':anat},file=sys.stderr)
    return {'func':func,'anat':anat}

def saveFile(projectName,anatFile,funcFile):
    folderPath = path.join("filePoint",projectName.split('.')[0])
    aFile = open(path.join(folderPath,"anatomical.nii"),"wb")
    aFile.write(anatFile)
    aFile.close()
    fFile = open(path.join(folderPath,"functional.nii"),"wb")
    fFile.write(funcFile)
    fFile.close()


@app.route("/listProjects",methods=['GET'])
@cross_origin()
def listProjectHandler():
    localPrjList = getProjects()
    resp = jsonify(list=localPrjList)
    return resp


@app.route("/newProject",methods=['POST'])
@cross_origin()
def newProjectHandler():
    file = request.files.get('connFile').read()
    projectName = request.headers.get('projectName')
    connProject = request.headers.get('connProject')
    paths = newProject(projectName,file,connProject)
    paths['success'] = True
    return jsonify(paths)


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


@app.route("/uploadProjectFiles",methods=['POST'])
@cross_origin()
def uploadProjectHandler():
    anatFile = request.files.get('anatomical').read()
    funcFile = request.files.get('functional').read()
    projectName = request.headers.get('projectName')
    saveFile(projectName,anatFile,funcFile)
    folderPath = path.join("filePoint",projectName.split('.')[0])
    jsonFile = path.join(folderPath,'info.json')
    with open(jsonFile, 'r') as file:
        data = json.load(file)
        data['status'] = 'calculating'
    with open(jsonFile, 'w') as file:
        json.dump(data, file)
    thread = Thread(target=workloadCalculateMatrix,args=(folderPath,))
    thread.start()
    return jsonify({'success':True}) 

@app.route('/data/<path:path>')
@cross_origin()
def send_volume(path):
    vals = path.split('@')
    k = 0
    if(len(vals)>1):
        projectName,k = vals
    else:
        projectName = vals[0]
    if(k == 0):
        fStr = 'filePoint/'+projectName+'/anatomical.nii'
    else:
        fStr = 'filePoint/'+projectName+'/cluster_'+str(k)+'_BIG.nii'
    print(fStr, file=sys.stderr)
    if exists(fStr):
        return send_from_directory('.', fStr)
    else:
        return "not found"

@app.route('/info/<path>')
@cross_origin()
def send_info(path):
    fStr = 'filePoint/'+path+'/info.json'
    data = '{}'
    with open(fStr) as fp:
        data = json.load(fp)
    return data

@app.route('/parcellate')
@cross_origin()
def parcellate():
    projectName = request.headers.get('projectName')
    k = request.headers.get('clusters')
    jsonFile = path.join("filePoint",projectName,'info.json')
    with open(jsonFile, 'r') as file:
        data = json.load(file)
        data['status'] = 'parcellating'
    with open(jsonFile, 'w') as file:
        json.dump(data, file)

    folderPath = path.join("filePoint",projectName)
    thread = Thread(target=workloadParcellate,args=(folderPath,int(k),))
    thread.start()
    return jsonify({'success':True})  

@app.route('/delete/<path>')
@cross_origin()
def remove_project(path):
    fStr = 'filePoint/'+path
    files = glob.glob(fStr+"/*")
    for f in files:
        remove(f)
    rmdir(fStr)
    return "done"

@app.route("/",methods=["GET"])
def stub():
    return "What are you doing here :|?"

if __name__ == "__main__":
    app.run(host='192.168.1.27', port=5000,debug=True)

    