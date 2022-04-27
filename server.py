#/usr/bin/python3
from crypt import methods
import base64
from curses.ascii import FS
import json
from logging import exception
from sre_constants import SUCCESS
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS, cross_origin

from os import listdir,mkdir,path,rmdir,remove
import glob
from os.path import exists
import sys

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

def newProject(projectName,file):
    folderPath = path.join("filePoint",projectName.split('.')[0])
    if not path.exists(folderPath):
        mkdir(folderPath,mode=0o777)
    if "gz" in projectName:
        f = open(path.join(folderPath,"anatomical.nii.gz"),"wb")
    else:
        f = open(path.join(folderPath,"anatomical.nii"),"wb")
    f.write(file)
    f.close()
    data = {
        "name":projectName,
        "status":"new", # new,ready, parcellating 
        "parc":['Исходный снимок'],
        "editable":"no",
    }
    with open(path.join(folderPath,'info.json'), 'w') as fp:
        json.dump(data, fp)


@app.route("/listProjects",methods=['GET'])
@cross_origin()
def listProjectHandler():
    localPrjList = getProjects()
    resp = jsonify(list=localPrjList)
    return resp


@app.route("/newProject",methods=['POST'])
@cross_origin()
def newProjectHandler():
    file = request.files.get('anatomical').read()
    projectName = request.headers.get('projectName')
    newProject(projectName,file)
    resp = jsonify(success=True)
    return resp

@app.route('/data/<path:path>')
@cross_origin()
def send_volume(path):
    fStr = 'filePoint/'+path+'/anatomical.nii'
    fStrGz = 'filePoint/'+path+'/anatomical.nii.gz'
    if exists(fStr):
        return send_from_directory('.', fStr)
    elif exists(fStrGz):
        return send_from_directory('.', fStrGz)
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

    