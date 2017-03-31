import os, os.path
from time import sleep

from trigger import Trigger

try:
    import execjs

    execjsAvalible = True
except:
    execjsAvalible = False
    execjs = None

import Vk_bot2
from DataTypes.LongPoolUpdate import LongPoolMessage, Updates
from DataTypes.group import group, contacts_group
from modules.__Command_template import C_template
from utils import ArgBuilder
from libs import VK_foaf


class Command_GetGroup(C_template):
    name = ['группа', 'groupinfo']
    access = ['user']
    perm = 'text.groupinfo'
    template = '{botname}, группа'

    @staticmethod
    def execute(bot: Vk_bot2.Bot, data: LongPoolMessage, Updates: Updates, forward=True):
        args = ArgBuilder.Args_message()
        args.peer_id = data.chat_id
        g = group.Fill(bot.UserApi.groups.getById(v='5.60', group_id=data.args[0],
                                                  fields=['city', 'country', 'place', 'description', 'wiki_page',
                                                          'members_count', 'counters', 'start_date', 'finish_date',
                                                          'can_post', 'can_see_all_posts', 'activity', 'status',
                                                          'contacts', 'links', 'fixed_post', 'verified', 'site',
                                                          'ban_info', 'cover'])[0])  # type: group
        ContactTemplate = "{} {} - {}. {}"
        GroupTemplate = 'Группа {}\n' \
                        'Кол-во участников {}\n' \
                        'Описание : {}\n' \
                        'Контактные данные:\n'
        contacts = []  # type: list[str]
        print(g.contacts)
        for contact in g.contacts:  # type: contacts_group
            print(contact)
            user = bot.GetUserNameById(contact.user_id)

            contacts.append(ContactTemplate.format(user.first_name, user.last_name, contact.desc,
                                                   contact.phone if contact.phone != None else ""))
            sleep(0.2)
        args.message = GroupTemplate.format(g.name, g.members_count, g.description) + '\n'.join(contacts)

        bot.Replyqueue.put(args.AsDict_())


class Command_Whois(C_template):
    name = ['whois']
    access = ['user']
    desc = 'Выводит информацию о вашем статусе и правах у бота'
    perm = 'text.whois'
    template = '{}, whois'

    @staticmethod
    def execute(bot: Vk_bot2.Bot, data: LongPoolMessage, LongPoolUpdates: Updates, forward=True):
        args = {"peer_id": data.chat_id, "v": "5.60", }
        if forward:
            args.update({"forward_messages": data.id})
        bb = data.text.split(' ')

        try:
            userperms = bot.USERS.GetPerms(bb[0])
            userstatus = bot.USERS.GetStatus(bb[0])
        except:
            userperms = "Не зарегестрирован"
            userstatus = "Не зарегестрирован"

        try:
            UD = VK_foaf.GetUser(bb[0])
        except:
            UD = {}
            UD['reg'] = "ОШИБКА"
            UD['Bday'] = "ОШИБКА"
            UD['gender'] = "ОШИБКА"
        userName = bot.GetUserNameById(int(bb[0]))

        msg_template = "Cтатус пользователя - {}\nЕго ФИО - {} {}\nЕго права :\n{}\nЗарегистрирован {}\nДень рождения {}\n пол {}\n"
        msg = msg_template.format(userstatus, userName.first_name, userName.last_name,
                                  ',\n'.join(userperms) if isinstance(userperms, list) else userperms, UD['reg'],
                                  UD['Bday'], UD['gender'])
        args['message'] = msg
        bot.Replyqueue.put(args)


class Command_AboutUser(C_template):
    name = ['whoami', "uname"]
    access = ['user']
    desc = 'Выводит информацию о вашем статусе и правах у бота'
    perm = 'text.whoami'
    template = '{}, whoami'

    @staticmethod
    def execute(bot: Vk_bot2.Bot, data: LongPoolMessage, LongPoolUpdates: Updates, forward=True):
        args = {"peer_id": data.chat_id, "v": "5.60", }
        if forward:
            args.update({"forward_messages": data.id})

        userperms = bot.USERS.GetPerms(data.user_id)
        userstatus = bot.USERS.GetStatus(data.user_id)
        UD = VK_foaf.GetUser(data.user_id)
        msg_template = "Ваш статус - {}\nВаш id - {}\nВаши права :\n{}\nЗарегистрирован {}\nДень рождения {}\n пол {}\nКол-во внутренней валюты: {}\n"
        msg = msg_template.format(userstatus, data.user_id, ',\n'.join(userperms), UD['reg'], UD['Bday'],
                                  UD['gender'], bot.USERS.GetCurrency(data.user_id))
        args['message'] = msg
        bot.Replyqueue.put(args)


class Command_EvalJS(C_template):
    enabled = execjsAvalible
    name = ['EvalJS']
    access = ['admin']
    desc = 'Выполняет JS скрипт'
    perm = 'core.EvJs'

    @staticmethod
    def execute(bot: Vk_bot2.Bot, data: LongPoolMessage, LongPoolUpdates: Updates, forward=True):
        args = {"peer_id": data.chat_id, "v": "5.60", }
        if forward:
            args.update({"forward_messages": data.id})
        code = bot.html_decode(' '.join(data.body.split('<br>')[1:]))
        JavaScript = execjs.get(execjs.runtime_names.Node)
        print('JavaScript runtime -- ', execjs.get().name)
        js = JavaScript.eval(code)

        args['message'] = 'Выполнено {}\n{}'.format(execjs.get().name, js)
        bot.Replyqueue.put(args)


class Command_ExecJS(C_template):
    enabled = execjsAvalible
    name = ['ExecJS']
    access = ['admin']
    desc = 'Выполняет JS скрипт, (вызываетмый метод - exec)'
    perm = 'core.ExJs'

    @staticmethod
    def execute(bot: Vk_bot2.Bot, data: LongPoolMessage, LongPoolUpdates: Updates, forward=True):
        args = {"peer_id": data.chat_id, "v": "5.60", }
        if forward:
            args.update({"forward_messages": data.id})
        code = bot.html_decode(' '.join(data.body.split('<br>')[1:]))
        JavaScript = execjs.get(execjs.runtime_names.Node)
        print('JavaScript runtime -- ', execjs.get().name)
        js = JavaScript.compile(code)
        js = js.call('exec')

        args['message'] = 'Выполнено {}\n{}'.format(execjs.get().name, js)
        bot.Replyqueue.put(args)


class Command_quit(C_template):
    name = ["shutdown"]
    access = ["admin"]
    desc = "Выключение бота"
    perm = 'core.shutdown'
    template = '{}, shutdown'

    @staticmethod
    def execute(bot: Vk_bot2.Bot, data: LongPoolMessage, LongPoolUpdates: Updates, forward=True):
        args = {"peer_id": data.chat_id, "v": "5.60", "forward_messages": data.id,
                "message": "Увидимся позже"}
        bot.Replyqueue.put(args)
        sleep(2)
        os._exit(0)


class Command_restart(C_template):
    name = ["рестарт"]
    access = ['admin']
    desc = "Рестарт бота"
    perm = 'core.restart'
    template = '{}, рестарт'

    @staticmethod
    def execute(bot: Vk_bot2.Bot, data: LongPoolMessage, LongPoolUpdates: Updates, forward=True):
        import sys
        os.execl(sys.executable, sys.executable, os.path.join(bot.ROOT, 'Vk_bot2.py'))


class Command_ExecCode(C_template):
    name = ["py", "python"]
    access = ['admin']
    desc = "Выполняет код из сообщения"
    perm = 'core.PY'
    template = '{}, py\nВаш код здесь'

    @staticmethod
    def execute(bot: Vk_bot2.Bot, data: LongPoolMessage, LongPoolUpdates: Updates, forward=True):
        args = {"peer_id": data.chat_id, "v": "5.60", }
        if forward:
            args.update({"forward_messages": data.id})
        code = bot.html_decode(data.body)
        code = '\n'.join(code.split('<br>')[1:]).replace('|', '  ')
        code = code.replace('print', 'print_')
        a = compile(code, '<string>', 'exec')
        from io import StringIO
        import contextlib, sys, traceback

        @contextlib.contextmanager
        def stdoutIO(stdout=None):
            old = sys.stdout
            if stdout is None:
                stdout = StringIO()
            sys.stdout = stdout
            yield stdout
            sys.stdout = old

        l = {'api': bot.UserApi, 'bot': bot}
        g = {'os': None}
        with stdoutIO() as s:
            try:
                exec(a, g, l)
            except:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                TB = traceback.format_tb(exc_traceback)

                args['message'] = "Не удалось выполнить, ошибка:{}\n {}\n {} \n {}".format(exc_type, exc_value,
                                                                                           ''.join(TB),
                                                                                           "Перешлите это сообщение владельцу бота")
                bot.Replyqueue.put(args)
                return
        template = """Принты:\n{}\nФинальный ответ:\n{}\n """
        out = template.format(s.getvalue(), str(l['out']) if 'out' in l else "None")
        args['message'] = out
        bot.Replyqueue.put(args)
        return True


import inspect


class Command_triggers(C_template):
    name = ['triggers']
    access = ['admin']
    desc = 'Выводит список тригеров'
    perm = 'core.triggers'

    @staticmethod
    def execute(bot: Vk_bot2.Bot, data: LongPoolMessage, Updates: Updates, forward=True):
        args = ArgBuilder.Args_message()
        args.peer_id = data.chat_id
        triggers = bot.TRIGGERS
        t = []  # type: list[str]
        trigger_template = 'Тригер №{}\n' \
                           'Условие : {}\n' \
                           'Таймаут : {}\n' \
                           'Одноразовый : {}\n' \
                           'Бесконечный : {}\n'
        for n, trigger in enumerate(triggers.triggers):  # type: (int,Trigger)
            lamb = inspect.getsource(trigger.cond)
            lamb = lamb[lamb.find('lambda'):lamb.find(',', lamb.find('lambda'))]
            t.append(trigger_template.format(n, lamb, trigger.timeout, trigger.onetime, trigger.infinite))
        args.message = '\n'.join(t)+'\n.'
        print(args.message)
        bot.Replyqueue.put(args.AsDict_())
