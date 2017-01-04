#! /usr/bin/python
# -*- coding: utf-8 -*-

import sys
G_ENABLE_RESETENCODING = True # 是否开启重新设置默认编码
if G_ENABLE_RESETENCODING:
    #Python IDLE reload(sys)后无法正常执行命令的原因
    #http://www.2cto.com/kf/201411/355112.html
    G_stdi,G_stdo,G_stde=sys.stdin,sys.stdout,sys.stderr
    reload(sys)
    sys.setdefaultencoding('utf8')
    sys.stdin,sys.stdout,sys.stderr = G_stdi,G_stdo,G_stde

import os.path
import traceback

### 添加自定义目录到Python的运行环境中
CUR_DIR_NAME = os.path.dirname(__file__)
def g_add_path_to_sys_paths(path):
    if os.path.exists(path):
        print('Add myself packages = %s' % path)
        sys.path.extend([path]) #规范Windows或者Mac的路径输入

try:
    path1 = os.path.normpath(os.path.abspath(os.path.join(CUR_DIR_NAME, 'self-site')))
    path2 = os.path.normpath(os.path.abspath(os.path.join(CUR_DIR_NAME, 'rs/self-site')))

    pathList = [path1, path2]
    for path in pathList:
        g_add_path_to_sys_paths(path)

except Exception as e:
    pass

### [End] 添加自定义目录到Python的运行环境中



import logging
import json
import tempfile

print os.path.normpath(tempfile.gettempdir())

##引入工具包
from tools.ExifImageRenamer import exifImageRenameCLI


## tornado 服务器部分代码
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
import tornado.escape
from tornado.options import define, options


define("port", default=8888, help="run on the given port", type=int)


import json

# 获取JSON字符串
def get_json_message(info):
    jsonData = None
    try:
        import jsonpickle
        jsonData = jsonpickle.encode(info)
    except ImportError:
        jsonData = json.dumps(info, separators=(',', ':'))

    return jsonData


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")


## print 重新定向
class __redirection__:

    def __init__(self):
        self.buff=''
        self.__console__=sys.stdout

    def write(self, output_stream):
        self.buff+=output_stream

    def to_console(self):
        sys.stdout=self.__console__
        print self.buff

    def to_file(self, file_path):
        f=open(file_path,'w')
        sys.stdout=f
        print self.buff
        f.close()

    def flush(self):
        self.buff=''

    def reset(self):
        sys.stdout=self.__console__



class ChatSocketHandler(tornado.websocket.WebSocketHandler):
    waiters = set()
    waitersMap = dict()
    cache = []
    cache_size = 200

    def allow_draft76(self):
        # for ios 5.0 safari
        return True

    def check_origin(self, origin):
        return True

    def open(self):
        print ("new client opened, client count = ", len(ChatSocketHandler.waiters))
        ChatSocketHandler.waiters.add(self)

    def on_close(self):
        print ("one client leave, client count = ", len(ChatSocketHandler.waiters))
        ChatSocketHandler.waiters.remove(self)
        ChatSocketHandler.waitersMap.pop(self)


    @classmethod
    def update_cache(cls, chat):
        cls.cache.append(chat)
        if len(cls.cache) > cls.cache_size:
            cls.cache = cls.cache[-cls.cache_size:]


    @classmethod
    def send_update(cls, chat):
        logging.info("sending message to %d waiters", len(cls.waiters))
        for waiter in cls.waiters:
            try:
                waiter.write_message(chat)
            except:
                logging.error("Error sending message", exec_info=True)



    @classmethod
    def send_updateWithId(cls, id, message):
        logging.info("sending message to id=%r waiter message=%r", id, message)
        for key, value in cls.waitersMap.items():
            if value == id:
                waiter = key
                waiter.write_message(message)

    def call_exifImageRenameCLI(self, taskInfo, user_id):
        if taskInfo['cli'] != 'ExifImageRenamer':
            return

        command = taskInfo['command']
        print command

        # 字符串转换到sys.argv
        for a in command:
            sys.argv.append(a)

        print sys.argv

        ## 处理核心
        data = None
        try:
            info = {
                'task_id': taskInfo['task_id'],
                'task_cli': taskInfo['cli'],
                'cb': taskInfo['callback'],
                'msg_type': 's_task_exec_running'
            }
            jsonStr = get_json_message(info)
            ChatSocketHandler.send_updateWithId(user_id, jsonStr)

            # call
            r_obj = __redirection__()
            sys.stdout = r_obj
            r_obj.to_console()

            data = exifImageRenameCLI()
        except Exception as e:
            import StringIO
            fp = StringIO.StringIO()
            traceback.print_exc(file=fp)
            traceback_message = fp.getvalue()
            info = {
                'task_id': taskInfo['task_id'],
                'task_cli': taskInfo['cli'],
                'cb': taskInfo['callback'],
                'msg_type':'s_err_progress',
                'content':e.__str__(),
                'traceback':traceback_message
            }
            jsonStr = get_json_message(info)
            ChatSocketHandler.send_updateWithId(user_id, jsonStr)
        else:
            if data is not None:
                #发送处理完毕的消息
                info = {
                    'task_id': taskInfo['task_id'],
                    'task_cli': taskInfo['cli'],
                    'cb': taskInfo['callback'],
                    'msg_type': 's_task_exec_result',
                    'result': data
                }
                ChatSocketHandler.send_updateWithId(user_id, get_json_message(info))


    def on_message(self, message):
        logging.info("got message %r", message)

        try:
            dictInfo = json.loads(message)
        except Exception as e:
            logging.info(e)
            dictInfo = eval(message)


        # 清理sys.argv,保证入口数据能够正常运行
        if sys.argv.count > 2:
            del sys.argv[1:]


        # 检查是否符合要求
        if not isinstance(dictInfo, dict):
            return

        # 信息处理{服务器使用s_作为前缀，客户端使用c_作为前缀}
        msg_type = dictInfo['msg_type']
        user_id = dictInfo['user_id']

        if  msg_type == 'c_notice_id_Info':
            ChatSocketHandler.waitersMap[self] = user_id

            info = {'msg_type':'s_get_id_Info'}
            jsonStr = get_json_message(info)

            ChatSocketHandler.send_updateWithId(user_id, jsonStr)

        elif msg_type == 'c_task_exec':
            taskInfo = dictInfo['taskInfo']
            self.call_exifImageRenameCLI(taskInfo, user_id)

            pass

        #ChatSocketHandler.send_update(message)

class EchoWebSocket(tornado.websocket.WebSocketHandler):
    def open(self):
        print "WebSocket opened"

    def on_message(self, message):
        self.write_message(u"You said: " + message)

    def on_close(self):
        print "WebSocket closed"

    def check_origin(self, origin):
        return True


def main():
    tornado.options.parse_command_line()

    # remove params --port=?
    param_port = '--port=' + str(options.port)
    if param_port in sys.argv:
        sys.argv.remove(param_port)

    # create application
    application = tornado.web.Application([
        (r"/", MainHandler),
        (r"/websocket", ChatSocketHandler)
    ])
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.port)
    print('start web server on port: ', options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()