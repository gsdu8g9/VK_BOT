import io
import queue
import re
import threading
import tkinter as tk
import urllib
from math import *
from random import choice
from time import sleep
from tkinter import ttk
from urllib.request import urlopen
import requests
import vk.exceptions as VKEX
from PIL import Image, ImageTk
from vk import *
import trigger
from DataTypes.LongPoolUpdate import *
from DataTypes.user import user
from DataTypes.group import group
from Module_Manager import *
from User_Manager import *
from libs.tempfile_ import *
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

        img = urlopen(captcha_image_url)
        print(img)
        a = TempFile(img.read(), 'jpg', NoCache=True)
        self.popup(a.path_)
        a.rem()
        # cap = input('capcha text:')
        return self.capchaVal

    def popup(self, img):
        img = Image.open(img)

        self.root = tk.Tk()
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
        self.capchaVal = self.capcha.get()
        self.root.destroy()


class Bot:
    def __init__(self, threads=4, LP_Threads=1, DEBUG=False):

        self.ROOT = getpath()
        self.IMAGES = os.path.join(self.ROOT, 'IMAGES')
        # self.Responder = Responder()
        self.Checkqueue = queue.Queue()
        self.Replyqueue = queue.Queue()
        self.LP_threads = []
        self.EX_threadList = []
        for i in range(threads):
            self.EX_threadList.append(threading.Thread(target=self.ExecCommands))
            self.EX_threadList[i].setDaemon(True)
            self.EX_threadList[i].start()
            print('Exec thread №{} started'.format(i))
        self.USERS = UserManager()
        self.MODULES = ModuleManager()
        self.DEBUG = DEBUG
        self.TRIGGERS = trigger.TriggerHandler()
        self.AdminModeOnly = False

        self.defargs = {"v": "5.60"}

        self.LoadConfig()
        self.SaveConfig()

        self.UserAccess_token = self.Settings['UserAccess_token']
        if 'GroupAccess_token' in self.Settings:
            self.GroupAccess_token = self.Settings['GroupAccess_token']
            self.GroupSession = SessionCapchaFix(access_token=self.GroupAccess_token)
            self.GroupApi = API(self.GroupSession)
        else:
            self.GroupApi = None

        self.UserSession = SessionCapchaFix(access_token=self.UserAccess_token)
        self.DefSession = SessionCapchaFix()

        self.UserApi = API(self.UserSession)
        self.DefApi = API(self.DefSession)

        self.log = io.open("Message_Log.Log", mode="ta", newline="\n", encoding="utf-8")

        self.ReplyThread = threading.Thread(target=self.Reply)
        self.ReplyThread.setDaemon(True)
        self.ReplyThread.start()

        self.MyUId = self.UserApi.users.get()[0]['uid']

        self.MyName = self.GetUserNameById(self.MyUId, update=True)

        print('LOADED')

    def GetImg(self, name) -> str:
        """

        Args:
            name: Image name

        Returns:
            str:Path to img
        """
        if name in os.listdir(self.IMAGES):
            return os.path.join(self.IMAGES, name)

        else:
            raise FileNotFoundError('There is no file named {} in images folder'.format(name))

    def GetUserFromMessage(self, message_id) -> str:
        """

        Args:
            message_id: Message id

        Returns:
            str:user id
        """

        uid = self.UserApi.messages.getById(message_ids=message_id, v="5.60")['items'][0]['user_id']
        return uid

    @staticmethod
    def html_decode(s):
        htmlCodes = (
            ("'", '&#39;'),
            ('"', '&quot;'),
            ('>', '&gt;'),
            ('<', '&lt;'),
            ('&', '&amp;')
        )
        for code in htmlCodes:
            s = s.replace(code[1], code[0])
        return s

    def GetUserNameById(self, Id, case='nom', update=False) -> user:

        """

        Args:
            update (bool): Use api instead of cached info
            Id (int): User ID
            case (str): case

        Returns:
            user:User data
        """
        print(Id, type_='GetUserNameById/DEBUG')
        if self.USERS.isCached(Id) and case == 'nom' and not update:
            print('Using cached data for user {}'.format(Id))
            User = self.USERS.getCache(str(Id))

        else:
            try:
                User = self.UserApi.users.get(user_ids=Id, v="5.60",
                                              fields=['photo_id', 'verified', 'sex', 'bdate', 'city', 'country',
                                                      'home_town', 'has_photo', 'photo_50', 'photo_100',
                                                      'photo_200_orig', 'photo_200', 'photo_400_orig', 'photo_max',
                                                      'photo_max_orig', 'online', 'domain',
                                                      'has_mobile', 'contacts', 'site', 'education', 'universities',
                                                      'schools', 'status', 'last_seen',
                                                      'followers_count', 'common_count', 'occupation', 'nickname',
                                                      'relatives', 'relation', 'personal',
                                                      'connections', 'exports', 'wall_comments', 'activities',
                                                      'interests', 'music', 'movies', 'tv',
                                                      'books', 'games', 'about', 'quotes', 'can_post',
                                                      'can_see_all_posts', 'can_see_audio', 'can_write_private_message',
                                                      'can_send_friend_request', 'is_favorite', 'is_hidden_from_feed',
                                                      'timezone', 'screen_name', 'maiden_name',
                                                      'crop_photo', 'is_friend', 'friend_status', 'career', 'military',
                                                      'blacklisted', 'blacklisted_by_me', 'first_name_nom',
                                                      'first_name_gen',
                                                      'first_name_dat', 'first_name_acc', 'first_name_ins',
                                                      'first_name_abl', 'last_name_nom', 'last_name_gen',
                                                      'last_name_dat',
                                                      'last_name_acc', 'last_name_ins', 'last_name_abl'])[0]
                self.USERS.cacheUser(Id, User)
            except Exception:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                TB = traceback.format_tb(exc_traceback)
                print(TB, exc_type, exc_value)
                User = None

        return user.Fill(User)

    def Reply(self):
        while True:
            args = self.Replyqueue.get()

            sleep(1)
            try:
                self.UserApi.messages.send(**args)
                self.Replyqueue.task_done()
            except VKEX.VkAPIError as Ex:
                sys.stderr.write('VkApi error - ' + str(Ex))
                self.Replyqueue.put(args)

    def generateConfig(self, path):
        token = input('User access token')
        self.USERS.WriteUser(input('Admin ID'), self.USERS.Stats.admin, self.USERS.Actions.Add, 'core.*', 'chat.*')
        data = {}
        with open(path + '/settings.json', 'w') as config:
            data['settings'] = {'UserAccess_token': token, "bannedCommands": {}}

            json.dump(data, config)

    def LoadConfig(self):
        path = getpath()
        if not os.path.exists(path + '/settings.json'):
            self.generateConfig(path)
        with open(path + '/settings.json', 'r') as config:
            settings = json.load(config)
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
            data['stat'] = self.Stat
            data['settings'] = self.Settings
            json.dump(data, config)

    def GetUploadServer(self):
        return self.UserApi.photos.getMessagesUploadServer()

    def UploadPhoto(self, urls) -> list:
        """

        Args:
            urls (list): list of strings ( urls )

        Returns:
            list: list of strings ( photo id )

        """
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

            if req.status_code == requests.codes.ok:
                try:
                    params = {'server': req.json()['server'], 'photo': req.json()['photo'], 'hash': req.json()['hash']}
                    photos = self.UserApi.photos.saveMessagesPhoto(**params)
                    for photo in photos:
                        atts.append(photo['id'])
                except:
                    continue
        return atts

    def UploadFromDisk(self, file) -> str:
        """

        Args:
            file (str):path to file

        Returns:
            str:photo id
        """
        try:
            self.Stat['cache'] = str(prettier_size((os.path.getsize(os.path.join(getpath(), 'tmp', 'cache.zip')))))
        except:
            self.Stat['cache'] = 'NO CACHE'
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
            except Exception as ex:
                print(ex.__traceback__)
                print(ex.__cause__)

                exc_type, exc_value, exc_traceback = sys.exc_info()
                TB = traceback.format_tb(exc_traceback)
                print(exc_type, exc_value, ''.join(TB))
                return None

        return photo['id']

    def UploadDocFromDisk(self, file) -> str:
        """

        Args:
            file (str):path to file

        Returns:
            str: doc id
        """
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

    def ExecCommands(self):

        def process_fwd_msg(message: LongPoolMessage) -> LongPoolMessage:
            if message.hasFwd:
                fwd = message.fwd_messages[0]

                if fwd.hasAttachment:
                    message.attachments.extend(fwd.attachments)
            return message

        from DataTypes.LongPoolUpdate import Updates

        def print_message(self, data: LongPoolMessage, LongPoolData: Updates):
            # print_(data)

            def process_attachments(_data: LongPoolMessage, _LongPoolData: Updates):
                fwdMessages = []
                attachments = []

                def process_FWD(fwds: list, depth=1):

                    for fwd in fwds:
                        # fwd = fwd_message()
                        if fwd.hasFwd:
                            process_FWD(fwd.fwd_messages, depth + 1)

                        templateFWD = '|{}{} : \n|{}| {}\n'
                        try:
                            try:
                                Tuser = _LongPoolData.GetUserProfile(fwd.user_id)
                                Tusr = Tuser.first_name + ' ' + Tuser.last_name
                                Tmsg = fwd.body.replace('<br>', '\n| ')
                                fwdMessages.append(
                                    templateFWD.format('    ' * fwd.depth, Tusr, ' ' + '    ' * fwd.depth, Tmsg))
                            except:
                                Tuser = self.USERS.getCache(fwd.user_id)
                                Tuser.first_name = Tuser['first_name']
                                Tuser.last_name = Tuser['last_name']
                                Tusr = Tuser.first_name + ' ' + Tuser.last_name
                                Tmsg = fwd.body.replace('<br>', '\n| ')
                                fwdMessages.append(
                                    templateFWD.format('    ' * fwd.depth, Tusr, ' ' + '    ' * fwd.depth, Tmsg))
                        except:
                            fwdMessages.append(templateFWD.format(' ', 'ERROR', '', 'ERROR'))
                            continue

                process_FWD(_data.fwd_messages)
                if _data.hasAttachment:
                    for t in _data.attachments:
                        if t.type == attachment.types.photo:
                            template_attach = "{} : {}"
                            attachments.append(template_attach.format(t.type, t.photo._getbiggest()))

                out = ''
                out += ''.join(fwdMessages) if len(fwdMessages) > 0 else ''
                out += '\n' if (len(fwdMessages) > 0) and (len(attachments) > 0) else ''
                out += ('Attachments :\n ' + '\n'.join(attachments[::-1])) if len(attachments) > 0 else ""
                out += '\n' if len(attachments) > 0 else ''
                return out

            try:
                user = LongPoolData.GetUserProfile(data.user_id)
                template = '{} : {} : \n| {}\n'

                template2 = '[ message_id : {} | peer_id : {} ]\n'

                subj = "PM" if "..." in data.title else data.title

                usr = user.first_name + ' ' + user.last_name

                msg = data.body.replace('<br>', '\n| ')

                attachments = process_attachments(data, LongPoolData)

                toPrint = template.format(subj, usr, msg) + attachments + template2.format(message.id,
                                                                                           message.chat_id) if self.DEBUG else '\n'
                print(toPrint, type_='message')
                self.log.write(toPrint)
                self.log.flush()
                os.fsync(self.log.fileno())
                # print(data)
            except Exception as ex:
                print(ex.__traceback__)
                print(ex.__cause__)

                exc_type, exc_value, exc_traceback = sys.exc_info()
                TB = traceback.format_tb(exc_traceback)
                print(exc_type, exc_value, ''.join(TB))
                pass

        while True:
            PvUpdates = self.Checkqueue.get()
            for message in PvUpdates.messages:
                if message.hasAction:
                    self.SourceAct(message, PvUpdates)
                sleep(0.3)
                self.TRIGGERS.processTriggers(message)
                self.Stat['messages'] += 1
                self.SaveConfig()
                if self.AdminModeOnly:
                    if 0 <= self.USERS.GetStatusId(message.user_id):
                        continue
                defargs = {"peer_id": message.chat_id, "v": "5.60", "forward_messages": message.id}
                p = '[\U0001F600-\U0001F64F]|[\U0001F300-\U0001F5FF]|[\U0001F680-\U0001F6FF]|[\U0001F1E0-\U0001F1FF]'
                emoji_pattern = re.compile(p, re.VERBOSE)

                message.body = emoji_pattern.sub('', message.body)
                print_message(self, message, PvUpdates)
                comm = message.body
                comm = comm.split("\n")
                temp = {}
                for C in comm[1:]:
                    C = str(C)
                    C = C.split(":")
                    temp[C[0].replace(" ", "").lower()] = ':'.join(C[1:])
                message.custom = temp

                pattern = "{}, ?|{}, ?|{}, ?|{}, ?".format(self.MyName.first_name.lower(), self.MyName.first_name,
                                                           'ред', "Ред")
                Command = str(re.split(pattern, comm[0])[-1])
                text = copy.deepcopy(Command)
                message.args = Command.split(' ')[1:]
                if (message.body.lower().startswith(self.MyName.first_name.lower())) or (
                        message.body.lower().startswith('ред')):

                    message = process_fwd_msg(message)

                    message.text = ' '.join(text.split(' ')[1:])

                    Command = Command.split(' ')[0]
                    if Command in self.Settings['bannedCommands']:
                        if message.chat_id in self.Settings['bannedCommands'][Command]:
                            self.Checkqueue.task_done()
                            return

                    if self.MODULES.isValid(Command):
                        funk = self.MODULES.GetModule(Command)
                        user = message.user_id
                        if self.USERS.HasPerm(user, funk.perms) and self.MODULES.CanAfford(self.USERS.GetCurrency(user),
                                                                                           Command):
                            try:
                                print("Trying to execute commnad {},\n arguments:{}".format(Command, message.args))
                                print(message)
                                stat = funk.funk.execute(self, message, PvUpdates)
                                self.USERS.pay(user, funk.cost)
                                if stat == False:
                                    print(self.MyName)
                                    defargs['message'] = 'Неправильно оформлен запрос. Пример запроса : {}'.format(
                                        funk.template.format(botname=self.MyName.first_name))
                                    self.Checkqueue.task_done()
                                    self.Replyqueue.put(defargs)
                                    continue
                                if stat == 'Error':
                                    pass
                                self.Checkqueue.task_done()
                                self.Stat['commands'] += 1
                                self.SaveConfig()
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

                                defargs['message'] = "Не удалось выполнить, ошибка:{}\n {}\n {} \n {}".format(exc_type,
                                                                                                              exc_value,
                                                                                                              ''.join(
                                                                                                                  TB),
                                                                                                              "Перешлите это сообщение владельцу бота")
                                print(defargs['message'])
                                # self.Reply(self.UserApi, args)
                                self.Checkqueue.task_done()
                                self.Replyqueue.put(defargs)
                        elif not self.MODULES.CanAfford(self.USERS.GetCurrency(user), Command):
                            defargs["message"] = "Нехватает валюты. Попробуйте обратиться к администрации"
                            self.Checkqueue.task_done()
                            self.Replyqueue.put(defargs)


                        else:
                            print('"Недостаточно прав"')
                            defargs["message"] = "Недостаточно прав"
                            self.Checkqueue.task_done()
                            self.Replyqueue.put(defargs)

                    else:
                        ans = self.Responder.respond(str(message.body), message.chat_id)
                        if ans == "":
                            continue
                        if ans == "IT'S HIGH NOON":
                            att = self.UploadFromDisk(choice([self.GetImg('Noon1.jpg'), self.GetImg('Noon2.jpg')]))
                            defargs['attachment'] = att
                        defargs['message'] = ans
                        self.Checkqueue.task_done()
                        self.Replyqueue.put(defargs)

    def SourceAct(self, data: LongPoolMessage, LongPoolUpdate: Updates):
        """

        Args:
            data (LongPoolMessage): Message
            LongPoolUpdate (LongPoolUpdate): Updates
        """
        print('Что то с Актом пришло')
        Targs = {"peer_id": data.chat_id, "v": "5.60"}
        if type == 'chat_photo_update':
            ChatAdmin = data.admin_id
            if int(ChatAdmin) != int(self.MyUId):
                return
            if int(data.user_id) == int(self.MyUId):
                return
            img = Image.open(os.path.join(self.IMAGES, 'CHAT_IMG.jpg'))
            tmpf = {'chat_id': int(data.chat_id) - 2000000000, "crop_x": ((img.size[0] - 350) / 2),
                    'crop_y': (((img.size[1] - 350) / 2) - 30), 'crop_width': 350}
            Uurl = self.UserApi.photos.getChatUploadServer(**tmpf)
            req = requests.post(Uurl['upload_url'], files={'file1': open(self.GetImg('CHAT_IMG.jpg'), 'rb')})
            self.UserApi.messages.setChatPhoto(**{'file': req.json()['response']})

        # if type == 'chat_title_update':
        #    who = data.user_id
        #    if self.USERS.HasPerm(who, 'chat.title'):
        #        if int(data.user_id) == int(self.MyUId):
        #            return
        #        if data.action. != data['source_text']:
        #            if data.chat_id in self.Settings['namelock']:
        #                self.UserApi.messages.editChat(chat_id=data.chat_id - 2000000000,
        #                                               title=data['source_old_text'], v='5.60')
        #                Targs['message'] = 'Название беседы менять запрещено'
        #                self.Replyqueue.put(Targs)
        #            else:
        #                pass
        #        else:
        #            pass

        if type == 'chat_invite_user':
            ChatAdmin = data.admin_id
            if int(ChatAdmin) != self.MyUId:
                return
            who = data.user_id  # Кто пригласил
            target = data.action.action_mid  # Кого пригласил

            if int(target) == self.MyUId or int(who) == self.MyUId:
                print('Сам себя')
                return
            if (not self.USERS.HasPerm(who, 'chat.invite')) or self.USERS.GetStatusId(target) < 99:
                Targs['message'] = 'Вы не имеете права приглашать людей в данную беседу'
                self.Replyqueue.put(Targs)
                name = self.GetUserNameById(int(target))
                Targs['message'] = "The kickHammer has spoken.\n {} has been kicked in the ass".format(
                    ' '.join([name['first_name'], name['last_name']]))
                self.UserApi.messages.removeChatUser(v=5.45, chat_id=data.chat_id - 2000000000, user_id=target)

            else:
                print('Приглашен администрацией')
        if type == 'chat_kick_user':
            if int(data.user_id) == int(self.MyUId):
                return

            if int(data.user_id) == int(data.action.action_mid):
                user = self.GetUserNameById(data.action.action_mid)
                print(user)
                try:
                    sex = user['sex']
                    if sex == 2:
                        end = ''
                    if sex == 1:
                        end = 'а'
                    else:
                        end = 'о'
                except:
                    end = 'о'
                Targs['message'] = 'Оп, {} {} ливнул{} с подливой &#9786;'.format(user['first_name'], user['last_name'],
                                                                                  end)
            else:
                user = self.GetUserNameById(data.action.action_mid, case='acc')
                Targs['message'] = 'Оп, {} {} кикнули &#127770;'.format(user['first_name'], user['last_name'])
            self.Replyqueue.put(Targs)

    def ContiniousMessageCheck(self, server=""):
        ts = 0
        key = 0
        while True:

            try:
                if (server == ''):
                    results = self.UserApi.messages.getLongPollServer()
                    server = results['server']
                    key = results['key']
                    ts = results['ts']

                url = 'https://{}?act=a_check&key={}&ts={}&wait=25&mode=2&version=1'
                try:
                    req = requests.request('GET', url.format(server, key, ts)).json()

                except Exception:
                    print('TIMEOUT ERROR, reconnecting in 5 seconds')
                    sleep(5)
                    server = ""
                    ts = ""
                    key = ""
                    continue
                if len(req['updates']) > 0:
                    hasMsg = False
                    for upd in req['updates']:
                        if 4 == upd[0]:
                            hasMsg = True
                    if hasMsg:
                        self.parseLongPoolHistory(ts)
                        ts = req['ts']
            except:
                print('TIMEOUT ERROR, reconnecting in 5 seconds')
                sleep(5)
                server = ""
                ts = ""
                key = ""

    def parseLongPoolHistory(self, ts):
        resp = self.UserApi.messages.getLongPollHistory(ts=ts, v='5.63',
                                                        fields=['photo_id', 'verified', 'sex', 'bdate', 'city',
                                                                'country', 'home_town', 'has_photo', 'photo_50',
                                                                'photo_100',
                                                                'photo_200_orig', 'photo_200', 'photo_400_orig',
                                                                'photo_max', 'photo_max_orig', 'online', 'domain',
                                                                'has_mobile', 'contacts', 'site', 'education',
                                                                'universities', 'schools', 'status', 'last_seen',
                                                                'followers_count', 'common_count', 'occupation',
                                                                'nickname', 'relatives', 'relation', 'personal',
                                                                'connections', 'exports', 'wall_comments', 'activities',
                                                                'interests', 'music', 'movies', 'tv',
                                                                'books', 'games', 'about', 'quotes', 'can_post',
                                                                'can_see_all_posts', 'can_see_audio',
                                                                'can_write_private_message',
                                                                'can_send_friend_request', 'is_favorite',
                                                                'is_hidden_from_feed', 'timezone', 'screen_name',
                                                                'maiden_name',
                                                                'crop_photo', 'is_friend', 'friend_status', 'career',
                                                                'military', 'blacklisted', 'blacklisted_by_me',
                                                                'first_name_nom', 'first_name_gen',
                                                                'first_name_dat', 'first_name_acc', 'first_name_ins',
                                                                'first_name_abl', 'last_name_nom', 'last_name_gen',
                                                                'last_name_dat',
                                                                'last_name_acc', 'last_name_ins', 'last_name_abl'], )
        try:
            updates = FillUpdates(resp)
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            TB = traceback.format_tb(exc_traceback)
            print(exc_type)
            print(exc_value)
            print('\n', '\n'.join(TB))
            return
        # print('\n', '\n'.join([str(m) for m in updates.messages]))
        self.Checkqueue.put(updates)

    def LeaveMeAlone(self, message: LongPoolMessage, result):
        defargs = {"peer_id": message.chat_id, "v": "5.60", "forward_messages": message.id}
        defargs['message'] = 'Оставьте меня. Мне нужно успокоится'
        print(message)
        # self.Replyqueue.put(defargs)


if __name__ == "__main__":
    bot = Bot(DEBUG=True)
    #t = trigger.Trigger(lambda message: (message.chat_id == 2000000025) and (message.user_id == 208128019),
    #                    callback=bot.LeaveMeAlone, onetime=False, infinite=True)
    #bot.TRIGGERS.addTrigger(t)
    bot.ContiniousMessageCheck()
