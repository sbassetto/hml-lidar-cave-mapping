#transportation:  
We recommand to protect the LiDAR with an on-purpose foam and place the computer box on a 5L caving bag. The button shoub be attached at the rear of the helmet

#Field process - recording
Once on the field apply the following process: 
1) Connect the LiDAR and attach the button
2) Open the box
3) Start the Battery
4) Close the Box and and place it on the bag
5) Once at the entrance of the cave, press the Button to start (ON)
6) IMMEDIATELY after WAIT STILL 15s (it is coded 5s, but with 15s you are sure that the DLIO will be able to compute proprelly)
7) Progress and try not to move too fast, do your best not to have brutal mouvements or head rotation. Don't be harsh with you if this happen. The recording is still in progress and you will get the opportunity to adapt the DLIO parameters afterward.
8) Once the acquisition complete, close it by turing the Button (OFF). On you way back to the car, let the computer process a little bit (several minutes) to alloow the storage to operate.
9) Open the box
10) Shut the battery off and close the box. 

#Field process - Data transfer and post-processing.
Once in your car or in a secured environment
1) Open your laptop and the box
2) verify the status of your batteries and enough space on the laptop. Connect to a power source if necessary (the transfer can take several hours) and make some space on your disk.
3) Open your phone config panel on "share your network". Your computer should be able to connect on it
4) Start the Battery of the LiDAR and wait 5s. The RPi should be able to connect on it
5) Open a terminal and verify if you can connect through a ssh protocol to the LiDAR.
  /ssh samuel@chinnok.local/ that was the command for the prototype. you will adapt it for your naming
6) Click on your laptop on 'mission-sync.sh' and let the process up. Don't stop it or do something else on your laptop (just to maximize the transfer). You should have 5 Terminals that open in your desktop (T1 : DLIO, T2: Rosbag play (@10% of the original pace ; this allow to the computer to compute all the files. DO NOT TRY TO INCLREASE ABOVE 20%), T3; Rosbridge connexion to foxglove, T4; recorgind of all topics (WARNING HUGE FILE), T5; terminal on the docker to verify that everything run smoothly)
7) Follow the instructions that appears on the screen and use the commands to verify that everything is ok. Open foxglove, open a rosbridge connexion and see slowly the /kfclouds and /deskwed points to appear in your screen. 
8) Once the transfer is done, the RPi is empty and ready to another field recording, shut off the battery.
9) Close the box.
10) WAIT until the rosbagplay has replayed once the recording, then the automatic topography starts
11) Verify that you have all your recordings.
