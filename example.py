#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time  
from flask import Flask  
from flask import g  
from flask import request  
from flask import Response  
from prometheus_client import Counter  
from prometheus_client import Summary
from prometheus_client import Gauge
from prometheus_client import generate_latest  
from prometheus_client import REGISTRY                       
from collections import deque
from copy import deepcopy

app = Flask(__name__)


# 请求数指标
REQ_COUNTER = Counter(
    "requests_total",            
    "How many HTTP requests processed, partitioned by status code and HTTP method.", 
    ["path", "status_code"],  
)
# 请求时延指标
REQ_DURATION = Summary(
    "request_duration_seconds", "The HTTP request latencies in seconds."
) 
# 程序使用最大队列长度
QUEUE_MAX_LEN = Gauge('queue_max_length', 'queue max size using by the function')

@app.route("/")
# 简单的业务逻辑：使用广度优先搜索找迷宫最短路径
def find_maze_path():  
    res,path = stack_maze(1,1,8,8)
    return str(maze).replace('],','],<br />') + "<br />From (1,1) to (8,8): " + str(res)\
        + "<br />Path:" + str(path)

@app.route("/metrics")
# 给Prometheus提供api接口
def metrics_api():  
    return Response(generate_latest(REGISTRY), mimetype="text/plain")

@app.before_request
# 请求前回调函数
def before_request_callback():  
    if request.path == "/metrics":
        return
    # 记录请求开始时间
    g._start_time = time.monotonic()

@app.after_request
# 请求后回调函数
def after_request_callback(response):  
    # 访问"/metrics"不计入
    if request.path == "/metrics":
        return response
    # 计算观测时间
    REQ_DURATION.observe(time.monotonic() - g._start_time)
    # 请求数加一
    REQ_COUNTER.labels(
        path=request.path, status_code=str(response.status_code)
    ).inc()
    return response

# 返回最短路径
def shortest_path(path):
    shortestpath = []
    curNode = path[-1]
    while curNode != path[0]:
        shortestpath.append((curNode[0],curNode[1]))
        curNode = path[curNode[2]]
    shortestpath.append((path[0][0],path[0][1]))
    shortestpath.reverse()
    return shortestpath
# 迷宫，0代表可走
maze = [
    [1,1,1,1,1,1,1,1,1,1],
    [1,0,0,1,0,0,0,1,0,1],
    [1,0,0,1,0,0,0,1,0,1],
    [1,0,0,0,0,1,1,0,0,1],
    [1,0,1,1,1,0,0,0,0,1],
    [1,0,0,0,1,0,0,0,0,1],
    [1,0,1,0,0,0,1,0,0,1],
    [1,0,1,1,1,0,1,1,0,1],
    [1,1,0,0,0,0,0,0,0,1],
    [1,1,1,1,1,1,1,1,1,1],
]
# 四个方向
dirs = [
    lambda x,y:(x+1,y),
    lambda x,y:(x-1,y),
    lambda x,y:(x,y+1),
    lambda x,y:(x,y-1),
]
# 简单的寻路算法
def stack_maze(x1,y1,x2,y2):
    qmxl = 0
    queue = deque()
    path = []
    queue.append((x1,y1,-1))
    maze_tmp = deepcopy(maze)
    maze_tmp[y1][x1] = -1
    while len(queue) > 0:
        # 更新使用的最大队列长度
        if len(queue) > qmxl:
            qmxl = len(queue)
        curNode = queue.popleft()
        path.append(curNode)
        if curNode[0] == x2 and curNode[1] == y2:
            # 到达终点
            print(shortest_path(path))
            QUEUE_MAX_LEN.set(qmxl)
            return (True,shortest_path(path))
        for dir in dirs:
            nextNode = dir(curNode[0],curNode[1])
            if maze_tmp[nextNode[1]][nextNode[0]] == 0 :
                # next node
                queue.append((*nextNode,len(path) -1))
                maze_tmp[nextNode[1]][nextNode[0]] = -1
    # 记录使用的最大队列长度
    QUEUE_MAX_LEN.set(qmxl)
    return (False,None)

if __name__ == "__main__":  
    app.run()
