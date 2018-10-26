#!/usr/bin/env python
# -*- coding: utf-8 -*-
import random
import string
import time
import signal
import os
import threading
import platform
import argparse
import requests
from ctypes import cdll
from enum import Enum
from flask import Flask, jsonify, request
from kazoo.client import KazooState
from kazoo.client import KazooClient

# ramoi = run at most one instance
# 通过zookeeper的锁机制实现某个程序在集群内最多只有一个实例同时运行
# 严格实现At Most One Instance语义，适合HA场景下只允许一个实例运行的情况
# 只支持linux平台


def randomstring(length):
    letters = string.ascii_letters
    return ''.join(random.choice(letters) for i in range(length))


PR_SET_PDEATHSIG = 1
CONNECTION_TIMEOUT = 5
SERVER_PORT = 9527
CLEAN_SERVICE_PATH = '/cleanService/' + randomstring(10)

zkLockThread = None


class State(Enum):
    INIT = 1
    ACTIVE = 2
    STANDBY = 3
    NEUTRAL = 4


class ConnectionState(Enum):
    DISCONNECTED = 1
    CONNECTED = 2
    TERMINATED = 3


def execService(cmd):
    try:
        servicePid = os.fork()
    except Exception as e:
        print(str(e))
        return -1

    # 父进程
    if servicePid != 0:
        return servicePid

    items = cmd.split(' ')
    try:
        result = cdll['libc.so.6'].prctl(PR_SET_PDEATHSIG, signal.SIGTERM)
        if result != 0:
            raise Exception('prctl failed with error code %s' % result)
        os.execvpe(items[0], tuple(items), os.environ)
    except Exception as e:
        print(str(e))
        # 如果exec执行失败，务必退出当前子进程
        os._exit(-1)


def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()


# 调用master节点的cleanService接口，停止master节点的服务
def clearOldMaster(url):
    try:
        r = requests.get(url, timeout=CONNECTION_TIMEOUT)
        if r.status_code == requests.codes.ok:
            return True
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
        print('Connect to master %s failed, %s' % (url, str(e)))
        return False
    except Exception as e:
        print('Connect to master %s failed, %s' % (url, str(e)))
        return False


class zk_rejoin_thread(threading.Thread):
    def __init__(self):
        super(zk_rejoin_thread, self).__init__()

    def run(self):
        url = 'http://' + platform.node() + ":" + str(SERVER_PORT) + CLEAN_SERVICE_PATH
        clearOldMaster(url)


# zk锁线程，用来竞争master节点并维持服务的运行
class zk_lock_thread(threading.Thread):
    def __init__(self, args):
        super(zk_lock_thread, self).__init__()
        self.zk = KazooClient(hosts=args.zk_hosts)
        self.zk.start()
        self.zk.add_listener(my_listener)

        # 互斥锁的地址，Master节点都需要先获取该锁
        self.lock_path = args.zk_root.rstrip('/') + "/" + args.service_name + "/MasterLock"
        # 获取锁成功的节点都需要创建sentry节点，用于master节点异常时其他节点回调清理接口
        self.sentry_path = args.zk_root.rstrip('/') + "/" + args.service_name + "/Sentry"
        self.identifier = platform.node() + ":" + str(os.getpid())
        self.lock = self.zk.Lock(self.lock_path, self.identifier)
        self.args = args
        self.version = -1
        self.service_pid = -1
        self.state = State.INIT
        self.running = True

    def cancel(self):
        self.lock.cancel()

    def release(self):
        self.lock.release()

    def version(self):
        return self.version

    def remove(self):
        if self.version >= 0:
            self.zk.delete(self.sentry_path, self.version)

    def killService(self, sig=signal.SIGTERM):
        if self.service_pid != -1:
            os.kill(self.service_pid, sig)

    def stop(self):
        self.running = False
        if self.service_pid != -1:
            os.kill(self.service_pid, signal.SIGTERM)
        else:
            self.cancel()

    def getServicePid(self):
        return self.service_pid

    def run(self):
        serviceRunCount = 0
        serviceFailCount = 0
        retryCount = 0

        while self.running:
            status = 0
            pid = -1

            try:
                cl = self.lock.contenders()
                print("Current lockers: ", cl)
                if len(cl) > 0 and cl[0] == self.identifier:
                    locked = True
                else:
                    locked = self.lock.acquire()

                print('enter lock state %s' % str(locked))
                # 尝试清理掉老的master节点
                if self.zk.exists(self.sentry_path):
                    csUrl = 'http://' + platform.node() + ":" + str(SERVER_PORT) + CLEAN_SERVICE_PATH
                    data, stat = self.zk.get(self.sentry_path)
                    # 如果之前的master不是自己，需要执行清理操作
                    if data != csUrl:
                        result = clearOldMaster(data)
                        retryCount = retryCount + 1
                        if not result and retryCount < args.master_max_retry:
                            time.sleep(min(10, 2**retryCount))
                            raise Exception('Clean master failed')
                        # 创建永久节点
                        self.version = self.zk.set(self.sentry_path, csUrl.encode(), stat.version).version
                        retryCount = 0
                else:
                    csUrl = 'http://' + platform.node() + ":" + str(SERVER_PORT) + CLEAN_SERVICE_PATH
                    self.zk.create(self.sentry_path, csUrl.encode(), makepath=True)
                    self.version = 0

                self.state = State.ACTIVE
                print('become ACTIVE, start service ...')
                self.service_pid = execService(args.start_service)

                if self.service_pid > 0:
                    pid, status = os.waitpid(self.service_pid, 0)
                    # 正常退出
                    if os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0:
                        serviceRunCount = serviceRunCount + 1
                        # 正常执行后清空失败计数器
                        serviceFailCount = 0
                    else:
                        serviceFailCount = serviceFailCount + 1

                    self.service_pid = -1
                else:
                    serviceFailCount = serviceFailCount + 1

                # 如果达到最大失败或者运行次数，退出
                if (args.service_max_fail >= 0
                        and args.service_max_fail <= serviceFailCount) or (args.service_max_run >= 0
                                                                           and args.service_max_run <= serviceRunCount):
                    self.running = False
                else:
                    time.sleep(1)

            except Exception as e:
                self.state = State.INIT
                print(str(e))
            finally:
                # 如果程序需要继续运行，不释放锁，直接重启程序即可
                if self.running and os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0:
                    print('exit without lock release, status: ', status)
                    pass
                else:
                    print('exit with lock release, status: ', status)
                    # 彻底退出，释放锁
                    try:
                        self.remove()
                        self.lock.release()
                    except Exception as e:
                        # zk连接遇到致命错误，安全起见退出程序
                        print(str(e))
                        break
        self.zk.stop()
        # zk线程退出
        csUrl = 'http://' + platform.node() + ":" + str(SERVER_PORT) + '/shutdown'
        requests.post(csUrl)


def my_listener(state):
    if state == KazooState.LOST:
        print("Zk connection Lost")
        # zk session已经丢失，停止当前的服务，重新去竞争master
        zrt = zk_rejoin_thread()
        zrt.setDaemon(True)
        zrt.start()
    elif state == KazooState.SUSPENDED:
        print("Zk connection Suspended")
    else:
        # 重新连接到了zk
        print("Zk connection Connected %s" % state)


def exitHandler(signum, frame):
    # 停止zk线程并退出程序
    zkLockThread.stop()
    print('Exit ramoi due to signal ', signum)


def create_app(args):
    app = Flask(__name__)

    @app.route(CLEAN_SERVICE_PATH, methods=['GET'])
    def clean():
        # 停止服务，5s后无法停止，强行杀掉进程
        cnt = 0
        pid = zkLockThread.getServicePid()
        while zkLockThread.getServicePid() != -1:
            if cnt > 5:
                zkLockThread.killService()
            else:
                zkLockThread.killService(sig=signal.SIGKILL)
            cnt = cnt + 1
            time.sleep(1)

        return jsonify({'status': 'ok', 'pid': pid})

    @app.route('/shutdown', methods=['POST'])
    def shutdown():
        shutdown_server()
        return 'Server shutting down...'

    return app


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='实现集群中单例运行某服务，适合HA系统。ramoi=Run At Most One Instance')
    parser.add_argument('service_name', type=str, help='服务名称')
    parser.add_argument('zk_root', type=str, help='zookeeper根路径')
    parser.add_argument('zk_hosts', type=str, help='zookeeper服务器列表，逗号分隔')
    parser.add_argument('--master_max_retry', default=3, type=int, help='连接master接口的最大次数，达到最大次数后认为master宕机，可以进行切换')
    parser.add_argument('--start_service', type=str, help='启动服务的命令')
    parser.add_argument('--service_max_fail', default=3, type=int, help='服务最大连续失败次数，达到次数限制后，控制进程也退出，-1表示无限制')
    parser.add_argument(
        '--service_max_run', default=1, type=int, help='服务最大运行次数，服务执行完毕后会自动重启运行，达到最大运行次数后控制进程也退出，-1表示无限制')

    args = parser.parse_args()

    # 初始zk
    zkLockThread = zk_lock_thread(args)
    zkLockThread.setDaemon(True)
    zkLockThread.start()

    # 正常退出程序时，清理东西
    signal.signal(signal.SIGTERM, exitHandler)
    signal.signal(signal.SIGINT, exitHandler)

    print('Clean service addr: ' + CLEAN_SERVICE_PATH)
    app = create_app(args)
    app.run(debug=False, host='0.0.0.0', port=SERVER_PORT)
