
# This code looks for a notepad file + retime image sequence. Based on the frame information encoded in the notepad file it creates a new retime camera that works with the retime sequence. 
# Notepad has to frame numbers only added line by line which only follows 4 digits pattern. 

import maya.cmds as cmds
import os
import time

# Duplicate & bake the selected camera so that there will be keys on every frames to copy . 
def duplicate_temp(sele):
    global dupli_test_cam , dupli_test_shape

    dupli_test_cam  = cmds.duplicate(sele, name = "Dupli_temp")
    dupli_test_shape = cmds.listRelatives(dupli_test_cam)

    cmds.parentConstraint(sele, dupli_test_cam)
    cmds.bakeResults( dupli_test_cam , time=(StartTime,EndTime), shape = True )

    cop_K = cmds.copyKey('%s.focalLength' %sele_shape[0])
    if cop_K:  
        cmds.pasteKey('%s.focalLength' %dupli_test_shape[0])

# will make  the 'Use Image Sequence ' box checked. 
def image_sequence(new_image, status):
    cmds.setAttr ('%s.useFrameExtension'  %new_image, status)

def delete_temp():
    cmds.delete(dupli_test_cam)
    cmds.delete(R_grp)

# copy paste the keys from the baked duplicate camera to the newly created Retime camera.
def retime(ret_frames, StartTime):

    retime_frames = []

    for i in ret_frames:

        # under the hood every notepad file will have an encoded \t\n to keep the lines one below other. split command will seperate that from the frames.
        tes = i.split('\r')
        
        # this converts the frames in to integer from string format. 
        frames = int(tes[0])
               
        retime_frames.append(frames)
        
        if len(retime_frames) >= 2:
            if not retime_frames[-2] <= frames:
                delete_temp()
                cmds.error(" frame %s from notepad might not be in an order " % frames )
                
        cop_K = cmds.copyKey( dupli_test_cam, time= (frames,frames))
        
        if cop_K:
            cmds.pasteKey( Rcam, time=(StartTime,StartTime))
        else:
            delete_temp()
            cmds.error(" frame %s is out of the main camera range" % frames)
        
        # the below line will jump one frame forward for the pasteKey . 
        StartTime += 1

# To add imageplane to the retime camera. we wil be choosing the retime image sequence from the second popup dialoge2. 
def setup_image(sele):

    Warning_message = "Source camera has NO imageplane. Skipping"

    source_image = cmds.listRelatives(cmds.listRelatives(sele))
    if source_image:
        
        # keeps a reasonable time span between the 2 popup boxes. 
        time.sleep(0.25)
        
        # storing the retime iamge sequence path
        ret_path = cmds.fileDialog2(fileMode=1, fileFilter="*.*", dialogStyle=2, cap = 'Pick an Image Sequence')

        source_image_shape = cmds.listRelatives(source_image)
        
        if ret_path:
            Rcam_cam_image, Rcam_cam_image_shape = cmds.imagePlane(camera = Rcam[0], fileName = ret_path[0])

            transfer_attr( source_image_shape, Rcam_cam_image_shape)
        
            image_sequence(Rcam_cam_image_shape, 1)
        else:
            cmds.warning("%s" %Warning_message)

    else:
        cmds.warning("%s" %Warning_message)

# Copying the original camera image depth to the retime camera image plane . 
def transfer_attr(source,child):
    cmds.copyAttr(source,child,values=True,at = 'depth')

# Locking the camera & group attributes
def lock_attr(cam_attr, cam, grp):
    for attr in cam_attr:
        cmds.setAttr('%s.%s' % (cam[0], attr) , lock = True)
    for i in cam_attr[:3]:
        cmds.setAttr('%s.%s' % (grp, i) , lock = True)

# catching the current start & end frames of the time line. 
StartTime = cmds.playbackOptions(q = True, animationStartTime = True)
EndTime = cmds.playbackOptions(q = True, animationEndTime = True)


sele = cmds.ls(selection = True)
if len(sele) != 1:
    cmds.error("Selection Error")
else:
    sele_shape = cmds.listRelatives(sele, shapes = True)
    if not sele_shape:
        cmds.error("Please select a camera")

if cmds.objectType(sele_shape) != 'camera':
    cmds.error("Please select a camera")


path = cmds.fileDialog2(fileMode=1, fileFilter="*.txt", dialogStyle=2, cap = 'Please pick a Notepad file')
if not path:
    cmds.error(" Please choose a source retime file")
    
cam_attr = ['translate', 'rotate', 'scale', 'focalLength', 'horizontalFilmAperture', 'verticalFilmAperture' ]

# Accessing the file path in read mode
ret_data = open(path[0], 'r' )

# This below line let us to read everything from the notepad file as a string line
ret_frames = ret_data.readlines()


duplicate_temp(sele)

Rcam = cmds.duplicate(sele, n = "MM_retime_came")
Rcam_shape = cmds.listRelatives(Rcam, shapes = True)

R_grp = cmds.group(n = 'reTime_camera', empty = True)
cmds.parent(Rcam, R_grp)



retime(ret_frames, StartTime)
setup_image(sele)  
lock_attr(cam_attr, Rcam, R_grp )

# deleting the temp camera that used to copy the keys from. 
cmds.delete(dupli_test_cam)

