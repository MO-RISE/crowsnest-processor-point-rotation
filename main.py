from copy import error
import logging
from typing import Any
import warnings
import json
import math
import numpy as np
import open3d as o3d
import random
import threading

from datetime import datetime, timezone
from streamz import Stream
from environs import Env
from paho.mqtt.client import Client as MQTT

from brefv_spec.envelope import Envelope


# Reading config from environment variables
env = Env()
MQTT_BROKER_HOST: str = env("MQTT_BROKER_HOST", "localhost")
MQTT_BROKER_PORT: int = env.int("MQTT_BROKER_PORT", 1883)
MQTT_CLIENT_ID: str = env("MQTT_CLIENT_ID", "processor-points")
MQTT_TRANSPORT: str = env("MQTT_TRANSPORT", "tcp")
MQTT_TLS: bool = env.bool("MQTT_TLS", False)
MQTT_USER: str = env("MQTT_USER", None)
MQTT_PASSWORD: str = env("MQTT_PASSWORD", None)
MQTT_TOPIC_IN_RADAR_SWEEP: str = env("MQTT_TOPIC_IN_RADAR_SWEEP", "CROWSNEST/SEAHORSE/RADAR/0/SWEEP")
MQTT_TOPIC_IN_LIDAR_SWEEP: str = env("MQTT_TOPIC_IN_LIDAR_SWEEP", "CROWSNEST/SEAHORSE/LIDAR/0/POINTCLOUD")
MQTT_TOPIC_IN_HEADING: str = env("MQTT_TOPIC_IN_HEADING", "CROWSNEST/SEAHORSE/GNSS/0/JSON")
MQTT_TOPIC_OUT_RADAR_NORTHUP: str = env("MQTT_TOPIC_OUT_RADAR_NORTHUP", "CROWSNEST/SEAHORSE/RADAR/0/NUP")
MQTT_TOPIC_OUT_LIDAR_NORTHUP: str = env("MQTT_TOPIC_OUT_LIDAR_NORTHUP", "CROWSNEST/SEAHORSE/LIDAR/0/NUP")


# Setup logger
LOG_LEVEL = env.log_level("LOG_LEVEL", logging.WARNING)
logging.basicConfig(level=LOG_LEVEL)
logging.captureWarnings(True)
warnings.filterwarnings("once")
LOGGER = logging.getLogger("crowsnest-processor-radar-north-up")


# Create mqtt client and configure it according to configuration
global mq


def to_brefv_raw(point_cloud):
    """Raw in message to brefv envelope"""

    msg, sensor_type = point_cloud

    envelope = Envelope(
        sent_at=datetime.now(timezone.utc).isoformat(),
        message=msg,
    )

    LOGGER.debug("Assembled into brefv envelope")
    return envelope.json(), sensor_type


def to_mqtt(brefv_msg: Any):
    """Publish a payload to a mqtt topic"""

    payload, payload_type = brefv_msg
    LOGGER.debug("Publishing on %s ", payload_type)

    if payload_type == "RADAR":
        try:
            mq.publish(
                MQTT_TOPIC_OUT_RADAR_NORTHUP,
                payload,
            )
        except Exception:  # pylint: disable=broad-except
            LOGGER.exception("Failed publishing RADAR to broker!")
    elif payload_type == "LIDAR":
        try:
            mq.publish(
                MQTT_TOPIC_OUT_LIDAR_NORTHUP,
                payload,
            )
        except Exception:  # pylint: disable=broad-except
            LOGGER.exception("Failed publishing LIDAR to broker!")


def on_message(client, userdata, message):
    LOGGER.info("New Message...")

    msg = message.payload.decode("utf-8")
    payload = json.loads(msg)
    topic = message.topic

    LOGGER.info(message.topic)

    if "message" in payload:
        msg = payload["message"]

        if topic == MQTT_TOPIC_IN_HEADING:
            source_heading.emit(float(msg["heading"]))

        else:  # Radar and LIDAR sweeps
            source.emit(msg)

def on_disconnect(client, userdata,  rc):
    LOGGER.warning("Disconnected from broker")
    mq.reconnect()
    
def on_connect(client, userdata, flags, rc):
    LOGGER.info("Connected to broker")
    mq.subscribe(MQTT_TOPIC_IN_LIDAR_SWEEP)
    mq.subscribe(MQTT_TOPIC_IN_RADAR_SWEEP)
    mq.subscribe(MQTT_TOPIC_IN_HEADING)

def rotate_points_azimuth(input_stream):
    """
    Rotate points along azimuth
    ----------------

    pcd_yxz: Points coordinates YXZ [[y1,x1,z1],[y2,x2,z2]...]
    degrees: float

    ### Return
    Rotated point cloud as a numpy array YXZ
    """
    # Map out variables
    point_coordinates, degrees = input_stream


    LOGGER.debug("Rotating to: %s", degrees) 
    degrees = -degrees 
    xy_or_xyz = len(list(point_coordinates["points"][0]))

    if xy_or_xyz == 2:  # Radar
        yxz = [[x, y, 0] for (x, y) in point_coordinates["points"]]  # Appending 0 to all elements
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(yxz)  # Array input format
        R = pcd.get_rotation_matrix_from_xyz((0, 0, math.radians(degrees)))
        pcd = pcd.rotate(R, center=(0, 0, 0))
        yxz_rotated = np.asarray(pcd.points).tolist()
        yxz_rotated = [[x, y] for (x, y, z) in yxz_rotated]
        # Passing radar targets weights along
        bref_radar_msg = {"points": yxz_rotated, "weights": point_coordinates["weights"]}
        return bref_radar_msg, "RADAR"

    elif xy_or_xyz == 3:  # LIDAR
        yxz = point_coordinates["points"]
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(yxz)  # Array input format
        R = pcd.get_rotation_matrix_from_xyz((0, 0, math.radians(degrees)))
        pcd = pcd.rotate(R, center=(0, 0, 0))
        yxz_rotated = np.asarray(pcd.points).tolist()
        return yxz_rotated, "LIDAR"

    else:
        LOGGER.exception("Can not find elements in sweep array")


if __name__ == "__main__":

    # Build pipeline
    LOGGER.info("Building pipeline...")

    # Point cloud
    global source
    source = Stream()
    # Heading
    global source_heading
    source_heading = Stream()

    # MQTT publish stream
    pipe_heading = source_heading.latest()
    pipe_rotate = source.zip(pipe_heading).map(rotate_points_azimuth).map(to_brefv_raw).sink(to_mqtt)

    ID_RANDOM = MQTT_CLIENT_ID + str(random.randint(1,999))
    mq = MQTT(client_id=ID_RANDOM, transport=MQTT_TRANSPORT)
    mq.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    if MQTT_TLS:
        mq.tls_set()
    mq.enable_logger(LOGGER)
    LOGGER.info("Connecting to MQTT broker...")
    mq.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT)

    LOGGER.info("Setting up MQTT listener...")

    mq.on_message = on_message
    mq.on_disconnect = on_disconnect
    mq.on_connect = on_connect
    mq.loop_forever()
    # threading.Thread(target=mq.loop_forever, daemon=True).start()