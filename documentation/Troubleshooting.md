# 📋 COMMAND MEMENTO                   

🛰️  CONNEXION CHINOOK :" 

 /ssh $RP_USER@$RP_HOST Password: chinook"/

🐳 DOCKER:
Statut: 

 /docker ps -a | grep $CONTAINER_NAME"/

Space: 

 /docker exec -it $CONTAINER_NAME df -h /root"/

🤖ROS 2 Verification (directly on the laptop)
Actives Topics: 

 /docker exec -it $CONTAINER_NAME bash -ic 'source /opt/ros/humble/setup.bash && ros2 topic list'/

LiDAR Freq 

 /docker exec -it $CONTAINER_NAME bash -ic 'source /opt/ros/humble/setup.bash && ros2 topic hz /livox/lidar'/

Odom freq: 

 /docker exec -it $CONTAINER_NAME bash -ic 'source /opt/ros/humble/setup.bash && ros2 topic hz /odom'/

📍 DLIO STATE:
Position (XYZ):

 /docker exec -it $CONTAINER_NAME bash -ic 'source /opt/ros/humble/setup.bash && ros2 topic echo /odom --once'/

Kill ROS:

 /docker exec -it $CONTAINER_NAME pkill -9 -f ros/

📍 DIAGNOSTIC CAVE EXPLORER:

Verify inclinason 

 /ros2 topic echo /odom --once"/

If z move while the helmet is still, gravity is not well calibrated

🧹 CHINOOK CLEANING

 /ssh $RP_USER@$RP_HOST 'sudo rm -rf ${RP_PATH}*'/

📂 Play another recording

/for folder in "$RAW_DIR"/*/; do
/    [ -e "$folder" ] || continue
/    BN=$(basename "$folder")
/    if [ "$BN" != "$LAST_BAG_NAME" ]; then  
/        echo "   -> $BN :"
/        echo "      docker exec -it $CONTAINER_NAME bash -ic 'source /opt/ros/humble/setup.bash && ros2 bag play $DOCKER_PATH/$BN --clock -r 0.05 --loop'"
/    fi
/done
