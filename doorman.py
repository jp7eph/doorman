#!/usr/bin/env python3
# coding: UTF-8
import argparse
from pysesame3.auth import CognitoAuth
from pysesame3.helper import CHSesame2MechStatus
from pysesame3.lock import CHSesame2
import ssl
import paho.mqtt.client as mqtt
import yaml
from pykwalify.core import Core
import sys


def on_connect(mqtt_client, userdata, flag, rc):
    """ブローカーに接続したときの処理。
    HomebridgeのSet Lock Target Stateを受信する。
    """
    print('Connected with result code ' + str(rc))  # 接続できた旨表示
    mqtt_client.subscribe([(set_target_topics, 0)])  # subするトピックを設定


def on_disconnect(mqtt_client, userdata, flag, rc):
    """ブローカーが予期せず切断したときの処理"""
    if rc != 0:
        print('Unexpected disconnection.')


def on_message(mqtt_client, userdata, msg):
    """HomebridgeのSet Lock Target Stateからメッセージを受信した際の処理。"""
    # NOTE for Debug
    # msg.topicにトピック名が，msg.payloadに届いたデータ本体が入っている
    # print("Received message '" + str(msg.payload) + "' on topic '" + msg.topic + "' with QoS " + str(msg.qos))
    payload = msg.payload.decode('utf-8')
    if payload == 'S':
        lock()
    elif payload == 'U':
        unlock()


def lock(history_tag='DOORMAN'):
    """SESAMEを施錠し、Get Lock Target Stateに対して[S]をPublishする。"""
    print("Recived LOCK request")
    mqtt_client.publish(get_target_topics, 'S')
    device.lock(history_tag=history_tag)
    print("LOCKED!")
    set_current_state_lock()


def unlock(history_tag='DOORMAN'):
    """SESAMEを解錠し、Get Lock Target Stateに対して[U]をPublishする。"""
    print("Recived UNLOCK request")
    mqtt_client.publish(get_target_topics, 'U')
    device.unlock(history_tag=history_tag)
    print("UNLOCKED!")
    set_current_state_unlock()


def set_current_state_lock():
    """Get Lock Current Stateに対して[S]をPublishする。"""
    mqtt_client.publish(get_target_topics, 'S')
    mqtt_client.publish(get_current_topics, 'S')
    print('Current state is Locked')


def set_current_state_unlock():
    """Get Lock Current Stateに対して[U]をPublishする。"""
    mqtt_client.publish(get_target_topics, 'U')
    mqtt_client.publish(get_current_topics, 'U')
    print('Current state is UnLocked')


def change_current_state(device: CHSesame2, status: CHSesame2MechStatus):
    """SESAME状態変更時のコールバック
    ロック状態に応じてset_current_state_lock/unlockを呼ぶ。
    """
    # XXX 既知のバグ: 遠隔操作時、変更前と変更後の2回呼ばれる。
    if status.isInLockRange():
        set_current_state_lock()
    elif status.isInUnlockRange():
        set_current_state_unlock()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="""Control SESAME3 from Homebridge by MQTT"""
    )
    parser.add_argument(
        '-c',
        '--config-file',
        default='./config.yaml',
        dest='config_file',
        help='the path to YAML config file. If not specified, defaut path(./config.yaml).'
    )
    parser.add_argument(
        '-s',
        '--schema-file',
        default='./schema.yaml',
        dest='schema_file',
        help='the path to schema file for YAML validation. If not specified, defaut path(./schema.yaml).'
    )
    args = parser.parse_args()

    with open(args.config_file, 'r') as yml:
        config = yaml.safe_load(yml)
    try:
        c = Core(source_file=args.config_file, schema_files=[args.schema_file])
        c.validate(raise_exception=True)
    except Exception as e:
        print(e)
        sys.exit(1)

    """ configからtopic名を読み込み """
    set_target_topics = config['homebridge']['set_target_state_topic']
    get_target_topics = config['homebridge']['get_target_state_topic']
    get_current_topics = config['homebridge']['get_current_state_topic']

    """ MQTTの初期化 """
    mqtt_client = mqtt.Client()
    if (config['mqtt']['username'] is not None) or (config['mqtt']['password'] is not None):
        mqtt_client.username_pw_set(
            username=config['mqtt']['username'], password=config['mqtt']['password'])
    if config['mqtt']['tls']['enable'] == True:
        mqtt_client.tls_set(
            ca_certs=config['mqtt']['tls']['cafile'],
            certfile=config['mqtt']['tls']['certfile'],
            keyfile=config['mqtt']['tls']['keyfile'],
            tls_version=ssl.PROTOCOL_TLSv1_2)
    mqtt_client.tls_insecure_set(True)
    # 接続、切断、受信時のコールバックを設定
    mqtt_client.on_connect = on_connect
    mqtt_client.on_disconnect = on_disconnect
    mqtt_client.on_message = on_message

    """ SESAMEの初期化 """
    auth = CognitoAuth(
        apikey=config['sesame']['api_key'],
        client_id=config['sesame']['client_id'],
    )
    device = CHSesame2(
        authenticator=auth,
        device_uuid=config['sesame']['uuid'],
        secret_key=config['sesame']['secret_key'],
    )

    mqtt_client.connect(config['mqtt']['broker'],
                        port=config['mqtt']['port'], keepalive=60)
    # SESAME状態変更時のコールバック
    device.subscribeMechStatus(change_current_state)
    # 起動時に解錠状態で初期化
    unlock()
    set_current_state_unlock()
    # 永久ループで受信待ち
    mqtt_client.loop_forever()
