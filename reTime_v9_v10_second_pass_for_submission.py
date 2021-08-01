
# This code looks for a notepad file + retime image sequence. Based on the frame information encoded in the notepad file it creates a new retime camera that works with the retime sequence. 
# Notepad has to frame numbers only added one below the other in ascending order. 

import maya.cmds as cmds
import os
import time

StartTime = cmds.playbackOptions(q = True, animationStartTime = True)
EndTime = cmds.playbackOptions(q = True, animationEndTime = True)
cam_attr = ['translate', 'rotate', 'scale', 'focalLength', 'horizontalFilmAperture', 'verticalFilmAperture' ]


# create, constrain & bake everyframes on a camera so that there will be keys on every frames to copy . 
def build_dummy_camera(sele):
    global Dummy_camera , Dummy_camera_shape

    Dummy_camera, Dummy_camera_shape = cmds.camera(n = 'Dupli_temp')

    P_constraint = cmds.parentConstraint(sele, Dummy_camera)
    transfer_channel_attr(sele_shape, Dummy_camera_shape, inConnections = False )
    cmds.connectAttr("%s.focalLength" %sele_shape[0], "%s.focalLength" % Dummy_camera_shape)
    cmds.bakeResults( Dummy_camera , time=(StartTime,EndTime), shape = True )
    cmds.delete(P_constraint)

# will make  the 'Use Image Sequence ' box checked. 
def image_sequence(new_image, status):
    cmds.setAttr ('%s.useFrameExtension'  %new_image, status)

# Using this function to delete all the temp assets from outliner incase if the process has to stop in the middle
def delete_temp():
    cmds.delete(Dummy_camera)
    cmds.delete(R_grp)

# Copy pasting the keys from the main camera to the dummy camera
def transfer_channel_attr(source,child, inConnections ):
    if inConnections:
        cmds.copyAttr(source,child,values=True,inConnections=True)
    else:
        cmds.copyAttr(source,child,values=True)

# processing the retime information and copy pasting the keys to the retime camera based on the notepad file.
def retime(ret_frames, StartTime):

    retime_frames = []
    try:
        for i in ret_frames:

            # under the hood every notepad file will have an encoded \t\n to keep the lines one below other. split command will seperate that from the frames.
            tes = i.split('\r')
            
            frames = int(tes[0])
    
            retime_frames.append(frames)
            
            if len(retime_frames) >= 2:
                if not retime_frames[-2] <= frames:
                    cmds.error(" error" )
            
            copy_focal = cmds.copyKey('%s.focalLength' %Dummy_camera_shape, time= (frames,frames))
            if copy_focal:  
                cmds.pasteKey('%s.focalLength' %Rcam_shape[0], time=(StartTime,StartTime))
                    
            cop_K = cmds.copyKey( Dummy_camera, time= (frames,frames))
            if cop_K:
                cmds.pasteKey( Rcam, time=(StartTime,StartTime))
            
            # the below line will jump one frame forward for the pasteKey . 
            StartTime += 1
    except:
        delete_temp()
        cmds.error("the value in the notepad is wrong")

# To add imageplane to the retime camera. we wil be choosing the retime image sequence from the second popup dialoge2. 
def setup_image(sele):

    Warning_message = "Source camera has NO imageplane. Skipping"

    source_image = cmds.listRelatives(cmds.listRelatives(sele))
    if source_image:
        
        # keeps a reasonable time span between the 2 popup boxes. 
        time.sleep(0.25)
        
        # storing the retime image sequence path
        ret_path = cmds.fileDialog2(fileMode=1, fileFilter="*.*", dialogStyle=2, cap = 'Pick an Image Sequence')

        source_image_shape = cmds.listRelatives(source_image)
        
        if ret_path:
            Rcam_cam_image, Rcam_cam_image_shape = cmds.imagePlane(camera = Rcam[0], fileName = ret_path[0])

            transfer_depth_attr( source_image_shape, Rcam_cam_image_shape)
        
            image_sequence(Rcam_cam_image_shape, 1)
        else:
            cmds.warning("%s" %Warning_message)

    else:
        cmds.warning("%s" %Warning_message)

# transferring the original camera image depth to the retime camera image plane . 
def transfer_depth_attr(source,child):
    cmds.copyAttr(source,child,values=True,at = 'depth')

# Locking the camera & group attributes
def lock_attr(cam_attr, cam, grp):
    for attr in cam_attr:
        cmds.setAttr('%s.%s' % (cam[0], attr) , lock = True)
    for i in cam_attr[:3]:
        cmds.setAttr('%s.%s' % (grp, i) , lock = True)

# Just running some basic checks to makesure we have the correct selection
def sanityCheck():
    global sele, sele_shape
    sele = cmds.ls(selection = True)
    if len(sele) != 1:
        cmds.error("Selection Error")
    else:
        sele_shape = cmds.listRelatives(sele, shapes = True)
        if not sele_shape:
            cmds.error("Please select a camera")

    if cmds.objectType(sele_shape) != 'camera':
        cmds.error("Please select a camera")

# setting up a retime camera , ready to paste the keys.
def build_retime_setup():
    global Rcam, Rcam_shape, R_grp

    Rcam = cmds.duplicate(Dummy_camera, n = "MM_retime_camera#")
    Rcam_shape = cmds.listRelatives(Rcam, shapes = True)

    R_grp = cmds.group(n = 'reTime_camera', empty = True)
    cmds.parent(Rcam, R_grp)

# Reading the notepad file and storing the informations under a variable
def read_file():
    path = cmds.fileDialog2(fileMode=1, fileFilter="*.txt", dialogStyle=2, cap = 'Please pick a Notepad file')
    if not path:
        cmds.error(" Please choose a source retime file")
        

    # Accessing the file path in read mode
    ret_data = open(path[0], 'r' )

    # This below line let us to read everything from the notepad file as a string line
    global ret_frames
    ret_frames = ret_data.readlines()


sanityCheck()
read_file()
build_dummy_camera(sele)
build_retime_setup()

retime(ret_frames, StartTime)
setup_image(sele)  
lock_attr(cam_attr, Rcam, R_grp )

# deleting the temp camera that used to copy the keys from. 
cmds.delete(Dummy_camera)

