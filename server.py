#!/usr/bin/python3

####
# 2022 Vladimir Andreev (andreev.va2010@yandex.ru)
# as a part of bachelor theses
# Server math side of web-based brain parcellation server 
#
# Functionality:
#   + handles user requests
#   + stores projects and files
#   + run methods, algorithms for brain parcellation 
#   
# This file is a flask server for web application.
# NOTE: print send data into stderr pipe for FLASK logging
#
####

import json
from logging import exception
from sre_constants import SUCCESS
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS, cross_origin
from threading import Thread
from newProjectHandler import newProject,saveFile
from evaluation import workloadCalculateMatrix,workloadParcellate

from os import listdir,path,rmdir,remove
import glob
from os.path import exists
import sys


app = Flask('__name__')
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

# internal method for getting available projects
# return: list of projects in working directory
def getProjects():
    result = listdir("filePoint/")
    return result

# method for handling listProject request
# return: sends to client list of available project in JSON style
@app.route("/listProjects",methods=['GET'])
@cross_origin()
def listProjectHandler():
    localPrjList = getProjects()
    resp = jsonify(list=localPrjList)
    return resp

# method for handling newProject request
# header:
#   projectName: name of new project
#   connProject: flag CONN/non-CONN file
# connFile: root file of CONN project
# return: JSON object with success=true if OK.
#         if the project is CONN based,
#         return JSON object will appended
#         with anatanomical (graymatter) and 
#         functional paths, to help user
#         load files.
@app.route("/newProject",methods=['POST'])
@cross_origin()
def newProjectHandler():
    file = request.files.get('connFile').read()
    projectName = request.headers.get('projectName')
    connProject = request.headers.get('connProject')
    paths = newProject(projectName,file,connProject)
    paths['success'] = True
    return jsonify(paths)

# method for handling uploadProjectFiles request
# header:
#   projectName: path where data will be stored.
#                actually only final folder, everything
#                else will be constructed in method
# anatomical: 3D graymatter file (already segmented, normalized, etc)
# functional: 4D fMRI file
# return: JSON object with success=true if OK.
#
# method performs project folder init, by
# storing original files, creating meta file with
# project info (info.JSON)
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
        data['status'] = 'setup'
    with open(jsonFile, 'w') as file:
        json.dump(data, file)
    return jsonify({'success':True}) 


# method for handling uploadProjectFiles request
# path: encoded string with desired data
#
# method return requested file for downloading or visualization.
# NOTE: encoded string desription
# http://SERVER/data/XXXX@YYYY[@ZZZZ]
# XXXX - file (project name)
# YYYY - "BIG" for anatomical quality
#        "NORM" for functrional quality (based on fMRI resolution)
# ZZZZ - percellations (if needed, otherwise will be original)
@app.route('/data/<path:path>')
@cross_origin()
def send_volume(path):
    vals = path.split('@')
    k = 0
    quality = ""

    print(vals, file=sys.stderr)
    projectName = vals[0]
    if(len(vals)>1):
        quality = vals[1]
    if(len(vals)>2):
        k = vals[2]
    else:
        projectName = vals[0]
    if(k == 0):
        fStr = 'filePoint/'+projectName+'/anatomical.nii'
    else:
        if(quality == 'BIG'):
            fStr = 'filePoint/'+projectName+'/cluster_'+str(k)+'_BIG.nii'
        elif(quality == 'RAW'):
            fStr = 'filePoint/'+projectName+'/anatomicalOrigin.nii'
        else:
            fStr = 'filePoint/'+projectName+'/cluster_'+str(k)+'.nii'
    print('Sent '+fStr, file=sys.stderr)
    if exists(fStr):
        return send_from_directory('.', fStr)
    else:
        return "not found"


# method for handling /info/ request
# path: encoded string with desired data (project name)
#
# send info.json of specific project to the client
@app.route('/info/<path>')
@cross_origin()
def send_info(path):
    fStr = 'filePoint/'+path+'/info.json'
    data = '{}'
    with open(fStr) as fp:
        data = json.load(fp)
    return data


# method for handling /parcellate request
# header:
#   projectName: name of the project
#             K: desired amount of clusters
#
# perform parcellation for the file projectName, tries to reach K clusters
@app.route('/parcellate')
@cross_origin()
def parcellate():
    projectName = request.headers.get('projectName')
    k = request.headers.get('clusters')
    jsonFile = path.join("filePoint",projectName,'info.json')
    with open(jsonFile, 'r') as file:
        data = json.load(file)
        data['status'] = 'parcellating'
        maskThresh = float(data['maskThresh'])
    with open(jsonFile, 'w') as file:
        json.dump(data, file)

    folderPath = path.join("filePoint",projectName)
    thread = Thread(target=workloadParcellate,args=(folderPath,int(k),maskThresh,))
    thread.start()
    return jsonify({'success':True})  


# method for handling /calcCorr request
# header:
#   projectName: name of the project
#    corrThresh: threshold for Pearson correlation value
#    maskThresh: threshold for mask voxel signal
#
# Calculate the correlation coefficients matrix
@app.route('/calcCorr')
@cross_origin()
def calcCorr():
    projectName = request.headers.get('projectName')
    corrThresh = float(request.headers.get('corrThresh'))
    maskThresh = float(request.headers.get('maskThresh'))

    jsonFile = path.join("filePoint",projectName,'info.json')
    with open(jsonFile, 'r') as file:
        data = json.load(file)
        data['status'] = 'calculating'
    data['corrThresh'] = corrThresh
    data['maskThresh'] = maskThresh
    with open(jsonFile, 'w') as file:
        json.dump(data, file)

    folderPath = path.join("filePoint",projectName)
    thread = Thread(target=workloadCalculateMatrix,args=(folderPath,corrThresh,maskThresh))
    thread.start()
    return jsonify({'success':True}) 


# method for handling /delete/ request
# path : project name
#
# Delete whole project folder from the server
@app.route('/delete/<path>')
@cross_origin()
def remove_project(path):
    fStr = 'filePoint/'+path
    files = glob.glob(fStr+"/*")
    for f in files:
        remove(f)
    rmdir(fStr)
    return "done"


# method for handling default request
# stub that returns sample data.
@app.route("/",methods=["GET"])
def stub():
    return "What are you doing here :|?"

if __name__ == "__main__":
    app.run(host='192.168.1.27', port=5000,debug=True)

    