import importlib
import inspect
import json
import os.path
import queue
import re
import sys
import threading
import tkinter as tk
import traceback
import urllib
from copy import copy
from math import *
from time import sleep
from tkinter import ttk
from urllib.request import urlopen

import aiml
import requests
from PIL import Image, ImageTk
from vk import *

from tempfile_ import *

HDR = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
    'Accept-Encoding': 'none',
    'Accept-Language': 'en-US,en;q=0.8',
    'Connection': 'keep-alive'}


def getpath():
    return os.path.dirname(os.path.abspath(__file__))


def prettier_size(n, pow=0, b=1024, u='B', pre=[''] + [p + 'i' for p in 'KMGTPEZY']):
    r, f = min(int(log(max(n * b ** pow, 1), b)), len(pre) - 1), '{:,.%if} %s%s'
    return (f % (abs(r % (-r - 1)), pre[r], u)).format(n * b ** pow / b ** float(r))


class SessionCapchaFix(Session):
    hdr = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
        'Accept-Encoding': 'none',
        'Accept-Language': 'en-US,en;q=0.8',
        'Connection': 'keep-alive'}

    def get_captcha_key(self, captcha_image_url):
        """
        Default behavior on CAPTCHA is to raise exception
        Reload this in child
        """
        print(captcha_image_url)
        img = urllib.request.Request(captcha_image_url, headers=self.hdr)
        a = TempFile(img, 'jpg', NoCache=True)
        self.popup(img)
        a.rem()
        # cap = input('capcha text:')
        return self.capcha.get()

    def popup(self, img):
        img = Image.open(img)

        self.root = tk.Toplevel()
        img = ImageTk.PhotoImage(image=img)

        Img = tk.Label(self.root)
        Img.pack()
        Img.configure(image=img)
        Img._image_cache = img
        self.capcha = ttk.Entry(self.root)
        self.capcha.pack()
        button = ttk.Button(self.root, command=self.Ret)
        button.pack()
        self.root.mainloop()

    def Ret(self):
        self.root.destroy()


class Bot:
    def __init__(self, threads=4, LP_Threads=4, ):
        self.defargs = {"v": "5.60"}
        self.LoadConfig()
        self.SaveConfig()
        self.kernel = aiml.Kernel()
        # if os.path.isfile("bot_brain.brn"):
        #    pass
        #    self.kernel.bootstrap(brainFile="bot_brain.brn")
        # else:
        #    pass
        #    self.kernel.bootstrap(learnFiles="startup.xml")
        #    self.kernel.bootstrap(learnFiles="1.xml")
        #    self.kernel.saveBrain("bot_brain.brn")
        self.kernel.bootstrap(learnFiles="startup.xml")
        self.kernel.bootstrap(learnFiles="1.xml")
        self.kernel.setTextEncoding('utf-8')
        self.Longpool = queue.Queue()
        self.Checkqueue = queue.Queue()
        self.Replyqueue = queue.Queue()
        self.UserAccess_token = self.Settings['UserAccess_token']
        self.UserSession = SessionCapchaFix(access_token=self.UserAccess_token)
        self.UserApi = API(self.UserSession)

        for _ in range(LP_Threads):
            self.LP = threading.Thread(target=self.parseLongPool)
            self.LP.setDaemon(True)
            self.LP.start()

        for _ in range(threads):
            self.t = threading.Thread(target=self.ExecCommands)
            self.t.setDaemon(True)
            self.t.start()

        self.ReplyThread = threading.Thread(target=self.Reply)
        self.ReplyThread.setDaemon(True)
        self.ReplyThread.start()

        self.MyUId = self.UserApi.users.get()[0]['uid']
        self.MyName = self.GetUserNameById(self.MyUId)
        self.Botmodules = {"filters": {}, "commands": {}}
        modules = os.listdir(os.path.join(getpath(), "modules"))
        sys.path.append(os.path.join(getpath(), "modules"))
        for module in modules:
            if not module.startswith("__"):
                module = importlib.import_module(str(module.split(".")[0]))
                for class_ in dir(module):
                    if class_.startswith("Filter"):
                        self.Botmodules['filters'][class_.split("_")[-1]] = getattr(module, class_)
                    if class_.startswith("Command"):
                        funk = getattr(module, class_)
                        self.Botmodules['commands'][funk.name] = getattr(module, class_)
                        #    def GetAliases(self):
                        #        path = getpath()
                        #        if not os.path.exists(path + '/aliases.json'):
                        #            return {}
                        #        else:
                        #            with open(path + '/aliases.json', 'r',encoding="utf-8") as alieses:
                        #                aliases = json.load(alieses)
                        #                return aliases
                        #    def SaveAlieses(self,data):
                        #        path = getpath()
                        #        with open(path + '/aliases.json', 'w') as alieses:
                        #            alieses.write(json.dumps(data,ensure_ascii=False))

    def GetUserFromMessage(self, message_id):
        sleep(0.25)

        try:
            uid = self.UserApi.messages.getById(message_id=message_id)[1]['uid']
            return uid
        except:
            sleep(1)
            uid = self.UserApi.messages.getById(message_id=message_id)[1]['uid']
            return uid

    def GetUserNameById(self, Id):
        sleep(0.1)
        try:
            User = self.UserApi.users.get(user_ids=Id, fields=['sex'])[0]
        except:
            return None
        return User

    def WaitForMSG(self, timer, args):
        print('WFM', args)
        try:
            user = args['data']['user_id']
            peer_id = args['data']['peer_id']
            old = True
        except:
            user = args['user_id']
            peer_id = args['peer_id']
            old = False
        for _ in range(timer):
            sleep(3)
            hist = self.UserApi.messages.getHistory(**{"peer_id": peer_id, "user_id": user, "count": 50, 'v': 5.38})

            for msg in hist['items']:
                try:

                    if (int(msg['from_id']) == int(user)) and (re.match(r'\d+$', msg['body'])):
                        if old:
                            if msg['date'] == args['data']['date']:
                                break
                        else:
                            if msg['date'] == args['date']:
                                print('Дошел до старого сообщения')
                                break

                        ans = int(msg['body'])
                        print(msg['body'])
                        return ans

                except:
                    continue

    def Reply(self):
        while True:
            args = self.Replyqueue.get()
            self.Replyqueue.task_done()
            sleep(1)
            try:
                self.UserApi.messages.send(**args)
            except Exception as Ex:
                print("error couldn't send message:", Ex)
                try:
                    args['message'] += '\nФлудконтроль:{}'.format(randint(0, 255))
                except:
                    args['message'] = '\nФлудконтроль:{}'.format(randint(0, 255))
                self.Replyqueue.put(args)

    def generateConfig(self, path):
        token = input('User access token')
        adminid = input('Admin vk id')
        data = {}
        with open(path + '/settings.json', 'w') as config:
            data['users'] = {'admin': [adminid]}
            data['settings'] = {'UserAccess_token': token}
            json.dump(data, config)

    def LoadConfig(self):
        path = getpath()
        if not os.path.exists(path + '/settings.json'):
            self.generateConfig(path)
        with open(path + '/settings.json', 'r') as config:
            settings = json.load(config)
            self.UserGroups = settings["users"]
            try:
                self.Stat = settings["stat"]
            except:
                self.Stat = {}
                self.Stat['messages'] = 0
                self.Stat['commands'] = 0
            self.Settings = settings["settings"]

    def SaveConfig(self):
        path = getpath()
        data = {}
        with open(path + '/settings.json', 'w') as config:
            data['users'] = self.UserGroups
            data['stat'] = self.Stat
            data['settings'] = self.Settings
            json.dump(data, config)

    def GetUploadServer(self):
        return self.UserApi.photos.getMessagesUploadServer()

    def UploadPhoto(self, urls):
        atts = []

        if type(urls) != type(['1', '2']):
            urls = [urls]
        i = 0
        for url in urls:
            i += 1
            print('downloading photo№{}'.format(i))
            server = self.GetUploadServer()['upload_url']
            req = urllib.request.Request(url, headers=HDR)
            img = urlopen(req).read()
            Tmp = TempFile(img, 'jpg')

            args = {}
            args['server'] = server
            print('uploading photo №{}'.format(i))
            req = requests.post(server, files={'photo': open(Tmp.file_(), 'rb')})
            print('Done')
            Tmp.rem()

            # req = requests.post(server,files = {'photo':img})
            if req.status_code == requests.codes.ok:
                # print('req',req.json())
                photo = 'photo' + str(i)
                try:
                    params = {'server': req.json()['server'], 'photo': req.json()['photo'], 'hash': req.json()['hash']}
                    photos = self.UserApi.photos.saveMessagesPhoto(**params)
                    for photo in photos:
                        atts.append(photo['id'])
                except:
                    continue
        return atts

    def UploadFromDisk(self, file):
        self.Stat['cache'] = str(prettier_size((os.path.getsize(os.path.join(getpath(), 'tmp', 'cache.zip')))))
        atts = []
        server = self.GetUploadServer()['upload_url']
        args = {}
        args['server'] = server

        print('uploading photo №')
        req = requests.post(server, files={'photo': open(file, 'rb')})

        print('Done')
        # req = requests.post(server,files = {'photo':img})
        if req.status_code == requests.codes.ok:
            # print('req',req.json())
            try:
                params = {'server': req.json()['server'], 'photo': req.json()['photo'], 'hash': req.json()['hash']}
                photo = self.UserApi.photos.saveMessagesPhoto(**params)[0]
            except:
                pass

        return photo['id']

    def UploadDocFromDisk(self, file):
        atts = []
        server = self.UserApi.docs.getUploadServer()['upload_url']
        args = {}
        args['server'] = server
        name = file.split('/')[-1]
        print('uploading file')
        req = requests.post(server, files={'file': open(file, 'rb')})
        print('Done')
        # req = requests.post(server,files = {'photo':img})
        if req.status_code == requests.codes.ok:
            # print('req',req.json())
            params = {'file': req.json()['file'], 'title': name, 'v': 5.53}
            doc = self.UserApi.docs.save(**params)[0]

            return 'doc{}_{}'.format(doc['owner_id'], doc['id']), doc
        return None, None

    def LongPool(self, key, server, ts):

        url = 'https://' + server + '?act=a_check&key=' + key + '&ts=' + str(ts) + '&wait=25&mode=130&version=1'
        try:

            request = requests.get(url)
            result = request.json()

        except ValueError:
            result = '{ failed: 2}'
        return result

    def ExecCommands(self):
        while True:
            data = self.Checkqueue.get()
            defargs = {"peer_id": data['peer_id'], "v": "5.60", "forward_messages": data['message_id']}
            print(data)
            if (data['message'].lower().startswith(self.MyName['first_name'].lower())) or (
                    data['message'].lower().startswith('ред')):
                comm = data["message"]
                comm = comm.split("<br>")
                args = {}
                temp = {}
                for C in comm[1:]:
                    C = C.split(":")
                    temp[C[0].replace(" ", "").lower()] = ':'.join(C[1:])
                args["custom"] = temp
                args.update(data)
                pattern = "{}, ?|{}, ?|{}, ?|{}, ?".format(self.MyName['first_name'].lower(), self.MyName['first_name'],
                                                           'ред', "Ред")
                Command = re.split(pattern, comm[0])[-1]
                text = copy(Command)
                args["text"] = text

                Command = Command.split(' ')[0]
                print(Command in self.Botmodules['commands'])
                if Command in self.Botmodules['commands']:
                    funk = self.Botmodules['commands'][Command]
                    user = data["user_id"]
                    print(self.GetUserGroup(data["user_id"]) in funk.access)
                    if ("all" in funk.access) or (self.GetUserGroup(user) in funk.access):
                        try:
                            print("Trying to execute commnad {},\n arguments:{}".format(Command, args))
                            funk.execute(self, args)
                        except Exception as Ex:

                            print(Ex.__traceback__)
                            print(Ex.__cause__)
                            sleep(1)
                            if 'many requests per second' in str(Ex):
                                print('Too many requests per second')
                                # self.Checkqueue.put(data,timeout=5)
                                continue
                            exc_type, exc_value, exc_traceback = sys.exc_info()
                            TB = traceback.format_tb(exc_traceback)
                            print("Не удалось выполнить, ошибка:{}\n {}\n {} \n {}".format(exc_type, exc_value,
                                                                                           ''.join(TB),
                                                                                           "Перешлите это сообение владельцу бота"))
                            defargs['message'] = "Не удалось выполнить, ошибка:{}\n {}\n {} \n {}".format(exc_type,
                                                                                                          exc_value,
                                                                                                          ''.join(TB),
                                                                                                          "Перешлите это сообение владельцу бота")
                            # self.Reply(self.UserApi, args)
                            self.Replyqueue.put(defargs)
                    else:
                        print('"Недостаточно прав"')
                        defargs["message"] = "Недостаточно прав"
                        self.Replyqueue.put(defargs)

    def GetUserGroup(self, id):
        for group in self.UserGroups.keys():
            if id in self.UserGroups[group]:
                return group
        return "user"

    def ContiniousMessageCheck(self, server=''):
        while True:
            if (server == ''):
                results = self.UserApi.messages.getLongPollServer()
                key = results['key']
                server = results['server']
                ts = results['ts']
            results = self.LongPool(key, server, ts)
            try:
                ts = results['ts']
            except (KeyError, TypeError):
                key = ''
                server = ''
                ts = ''
                sleep(0.001)
                continue
            try:
                updates = results['updates']
            except (KeyError, TypeError):
                key = ''
                server = ''
                ts = ''
                sleep(0.001)
                continue
            self.Longpool.put(results)

    def GetBiggesPic(self, att, mid):
        try:
            data = self.UserApi.photos.getById(photos=att, v=5.57)[0]
        except:

            print('using MID')
            data = self.UserApi.messages.getById(message_ids=mid, v=5.57)['items'][0]['attachments']
            print('mid data', data)
            # self.LOG('log',sys._getframe().f_code.co_name, 'mid data', data)
            for i in data:

                if i['type'] == 'photo' and (int(i['photo']['id']) == int(att.split('_')[1])):
                    key = i['photo']['access_key']
                    data = self.UserApi.photos.getById(photos=att, v=5.57, access_key=key)[0]

        print(data)
        sizes = re.findall(r'(?P<photo>photo_\d+)', str(data))
        print(sizes)
        sizesToSort = {int(size.split('_')[1]): size for size in sizes}

        sizesSorted = sorted(sizesToSort, reverse=True)[0]
        size = data[sizesToSort[sizesSorted]]
        print(size)
        return data[sizesToSort[sizesSorted]]

    def parseLongPool(self):
        while True:
            results = self.Longpool.get()
            try:
                updates = results['updates']
            except (KeyError, TypeError):
                key = ''
                server = ''
                ts = ''
                sleep(0.001)
                continue
            try:
                updates = results['updates']
            except (KeyError, TypeError):
                key = ''
                server = ''
                ts = ''
                sleep(0.001)
                continue
            if updates:
                for update in updates:
                    s = update

                    try:
                        code = s[0]
                    except KeyError:
                        continue
                    if code == 4:
                        try:
                            args = {}
                            message_id = s[1]
                            flags = s[2]
                            from_id = s[3]
                            timestamp = s[4]
                            subject = s[5]
                            text = s[6]
                            atts = s[7]
                            attatchments = []
                            try:
                                rand_id = int(atts[-1])
                            except:
                                rand_id = None
                            attsFindAll = re.findall(r'attach\d+_type', str(atts))
                            for att in attsFindAll:

                                if atts[att] == 'photo':
                                    attatchments.append(atts[att.split('_')[0]])
                            args['attachments'] = attatchments
                            args['peer_id'] = from_id
                            args["message"] = text
                            args['message_id'] = message_id
                            args['date'] = timestamp
                            args['user_id'] = self.GetUserFromMessage(message_id)
                            args['atts'] = atts
                            args['subject'] = subject
                            args['v'] = 5.45
                            if text == '!':
                                continue
                            if args['user_id'] != self.MyUId and rand_id == None:
                                self.Checkqueue.put(args, timeout=60)
                                # self.CheckForCommands(args)
                                # self.Reply(self.UserApi,args)
                                # return from_id,text,subject
                        except KeyError:
                            continue
                    elif code == 8:
                        try:
                            user = self.GetUserNameById(s[1] * -1)
                            try:
                                if user['sex'] == 2:
                                    sex = 'Вошел'
                                elif user['sex'] == 1:
                                    sex = 'Вошла'
                            except:
                                sex = 'Вошло'
                            toprint = " ".join([user['first_name'], user['last_name'], ' {} в сеть'.format(sex)])
                        except KeyError:
                            continue
                    elif code == 9:

                        try:

                            user = self.GetUserNameById(s[1] * -1)
                            try:
                                if user['sex'] == 2:
                                    sex = 'Вышел'
                                elif user['sex'] == 1:
                                    sex = 'Вышла'
                                else:
                                    sex = "Вышло"


                            except:
                                sex = 'Вышло'
                            try:
                                toprint = " ".join([user['first_name'], user['last_name'], ' {} из сети'.format(sex)])
                            except:
                                pass
                        except KeyError:
                            continue
                    elif code == 61:

                        try:
                            user = self.GetUserNameById(s[1])
                            toprint = " ".join([user['first_name'], user['last_name'], 'Набирает сообщение'])
                        except:
                            continue
                    elif code == 62:
                        user = self.GetUserNameById(s[1])

                        arg = {}
                        arg['chat_id'] = s[2]

                        try:
                            chat = self.UserApi.messages.getChat(**arg)
                        except:
                            chat = {}
                            chat['title'] = 'Хз чё, но тута ошибка'

                        try:
                            toprint = " ".join(
                                [user['first_name'], user['last_name'], 'Набирает сообщение в беседе', chat['title']])
                        except:
                            continue
                    elif code == 51:
                        try:
                            Targs = {}
                            id = str(s[1] + 2000000000)
                            if self.Settings['namelock'][id][1]:
                                chat = self.UserApi.messages.getChat(chat_id=s[1], v=5.57)['title']
                                if chat == self.Settings['namelock'][id][0]:
                                    continue
                                self.UserApi.messages.editChat(chat_id=s[1], title=self.Settings['namelock'][id][0],
                                                               v=5.57)
                                Targs['peer_id'] = id
                                Targs['v'] = 5.45
                                Targs['message'] = 'Название беседы менять запрещено'
                                self.Replyqueue.put(Targs)
                        except:
                            pass


bot = Bot()
print(bot.Botmodules)
bot.ContiniousMessageCheck()
