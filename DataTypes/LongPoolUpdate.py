class Updates:
    history = []
    messages = []
    profiles = []
    chats = []
    new_pts = 0
    def __str__(self):
        return str(dict({var:vars(self)[var] for var in vars(self)}))
    def AsDict(self):
        return {var:vars(self)[var] for var in vars(self)}
class action:
    class types:
        chat_kick_user = 'chat_kick_user'
        chat_title_update = 'chat_title_update'
        chat_invite_user = 'chat_invite_user'
        chat_photo_update = 'chat_photo_update'

    action = ''
    action_text = ''
    action_mid = 0
    def __str__(self):
        return str(dict({var:vars(self)[var] for var in vars(self)}))
    def AsDict(self):
        return {var:vars(self)[var] for var in vars(self)}

class LongPoolMessage:
    id = 0
    date = 0
    out = 0
    user_id = 0
    read_state = 0
    title = ''
    body = ''
    chat_id = 0
    chat_active = []
    action = action
    users_count = 0
    admin_id = 0
    def __str__(self):
        return str(dict({var:vars(self)[var] for var in vars(self)}))
    def AsDict(self):
        return {var:vars(self)[var] for var in vars(self)}
    # source_act = Source_act


class profile:
    id = 0
    first_name = ''
    last_name = ''
    sex = 0
    screen_name = ''
    online = 0
    online_app = 0
    online_mobile = 0
    def __str__(self):
        return str(dict({var:vars(self)[var] for var in vars(self)}))
    def AsDict(self):
        return {var:vars(self)[var] for var in vars(self)}

class chat:
    id = 0
    type_ = ''
    title = ''
    admin_id = 0
    users = []
    def __str__(self):
        return str(dict({var:vars(self)[var] for var in vars(self)}))
    def AsDict(self):
        return {var:vars(self)[var] for var in vars(self)}



class LongPool:
    ts = 0
    updates = Updates


def FillUpdates(resp):
    a = Updates()
    a.history = resp['history']
    for message in resp['messages']['items']:
        tMessage = LongPoolMessage()
        tMessage.id = message['id']
        tMessage.date = message['date']
        tMessage.user_id = message['user_id']
        tMessage.read_state = message['read_state']
        tMessage.title = message['title']
        tMessage.body = message['body']
        tMessage.chat_id = message['chat_id']
        tMessage.chat_active = message['chat_active']
        tMessage.users_count = message['users_count']
        tMessage.admin_id = message['admin_id']
        if 'action' in message:
            tAction = action()
            tAction.action = message['action']
            if tAction.action == tAction.types.chat_title_update:
                tAction.action_text = message['action_text']
            if tAction.action == tAction.types.chat_invite_user:
                tAction.action_mid = message['action_mid']
            if tAction.action == tAction.types.chat_kick_user:
                tAction.action_mid = message['action_mid']

        a.messages.append(tMessage)
    for Userprofile in resp['profiles']:
        tProfile = profile()
        tProfile.first_name = Userprofile['first_name']
        tProfile.last_name = Userprofile['last_name']
        if 'sex' in Userprofile:
            tProfile.sex = Userprofile['sex']
        tProfile.screen_name = Userprofile['screen_name']
        tProfile.online = Userprofile['online']
        if 'online_app' in Userprofile:
            tProfile.online_app = Userprofile['online_app']
        if 'online_mobile' in Userprofile:
            tProfile.online_mobile = Userprofile['online_mobile']
        a.profiles.append(tProfile)
    for c in resp['chats']:
        tChat = chat()
        tChat.id = c['id']
        tChat.type = c['type']
        tChat.title = c['title']
        tChat.admin_id = c['admin_id']
        tChat.users = c['users']

    return a