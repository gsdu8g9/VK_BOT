from DataTypes.Attachments import *
class action:
    class types:
        chat_kick_user = 'chat_kick_user'
        chat_title_update = 'chat_title_update'
        chat_invite_user = 'chat_invite_user'
        chat_photo_update = 'chat_photo_update'

    def __init__(self):
        self.action = ''
        self.action_text = ''
        self.action_mid = 0

    def __str__(self):
        return str(dict({var: str(vars(self)[var]) for var in vars(self)}))


    def AsDict(self):
        return {var: vars(self)[var] for var in vars(self)}




class LongPoolMessage:
    def __init__(self):
        self.id = 0
        self.date = 0
        self.out = 0
        self.user_id = 0
        self.title = ''
        self.body = ''
        self.chat_id = 0
        self.chat_active = []
        self.action = action
        self.hasAction = False
        self.fwd_messages = []
        self.users_count = 0
        self.admin_id = 0
        self.custom = {}
        self.attachments = []
        self.isChat = False
        self.hasAttachment = False
        self.text = ''
        self.args = []
    def __str__(self):
        return str(dict({var: str(vars(self)[var]) for var in vars(self)}))

    def AsDict(self):
        return {var: vars(self)[var] for var in vars(self)}
        # source_act = Source_act


class profile:
    def __init__(self):
        self.id = 0
        self.first_name = ''
        self.last_name = ''
        self.sex = 0
        self.screen_name = ''
        self.online = 0
        self.online_app = 0
        self.online_mobile = 0

    def __str__(self):
        return str(dict({var: str(vars(self)[var]) for var in vars(self)}))

    def AsDict(self):
        return {var: vars(self)[var] for var in vars(self)}


class chat:
    def __init__(self):
        self.id = 0
        self.type_ = ''
        self.title = ''
        self.admin_id = 0
        self.users = []

    def __str__(self):
        return str(dict({var: str(vars(self)[var]) for var in vars(self)}))

    def AsDict(self):
        return {var: vars(self)[var] for var in vars(self)}


class Updates:
    def __init__(self):
        self.history = []
        self.messages = []
        self.profiles = []
        self.chats = []
        self.new_pts = 0

    def GetUserProfile(self, id: int) -> profile:
        """

        Args:
            id (int): User ID

        Returns:
            profile
        """
        for user in self.profiles:
            if user.id == id:
                return user

    def GetChat(self, id: int) -> chat:
        """

        Args:
            id (int): Chat ID

        Returns:
            chat
        """
        for Chat in self.chats:
            if Chat.id == id:
                return Chat

    def __str__(self):
        return str(dict({var: str(vars(self)[var]) for var in vars(self)}))

    def AsDict(self):
        return {var: vars(self)[var] for var in vars(self)}

class fwd_message:
    def __init__(self):
        self.user_id = 0
        self.date = 0
        self.body = ''
        self.fwd_messages = []
        self.hasFwd = False
        self.depth = 1
    def __str__(self):
        return str(dict({var: str(vars(self)[var]) for var in vars(self)}))

    def AsDict(self):
        return {var: vars(self)[var] for var in vars(self)}
def FillUpdates(resp) -> Updates:
    """

    Args:
        resp (dict): LongPoolHistory response
    """
    def RecirsionFwd(fwd:dict,depth = 1) -> fwd_message:
        tFwd = fwd_message()
        tFwd.user_id = fwd['user_id']
        tFwd.date = fwd['date']
        tFwd.body = fwd['body']
        tFwd.depth = depth
        if 'fwd_messages' in fwd:
            tFwd.hasFwd = True
            for fwd2 in fwd['fwd_messages']:
                tFwd.fwd_messages.append(RecirsionFwd(fwd2,depth+1))
        return tFwd
    a = Updates()
    a.history = resp['history']
    for message in resp['messages']['items']:
        tMessage = LongPoolMessage()
        tMessage.id = message['id']
        tMessage.date = message['date']
        tMessage.user_id = message['user_id']
        tMessage.title = message['title']
        tMessage.body = message['body']
        if 'attachments' in message:
            tMessage.hasAttachment = True
            for attachment in message['attachments']:
                    tAttachment = Attachment()
                    tAttachment.type = attachment['type']
                    if tAttachment.type == Attachment.types.photo:
                        photo  = attachment['photo']
                        tPhoto = Attachment.Photo()
                        tPhoto.access_key = photo['access_key']
                        tPhoto.id = photo['id']
                        tPhoto.album_id = photo['album_id']
                        tPhoto.owner_id = photo['owner_id']
                        size = 0
                        for ph in photo:
                            if ph.startswith('photo'):
                                t = ph.split('_')[-1]
                                if size < int(t):
                                    size = int(t)
                        tPhoto.photo = photo['photo_{}'.format(size)]
                        tAttachment.photo = tPhoto
                    tMessage.attachments.append(tAttachment)

        if 'fwd_messages' in message:
            for fwd in message['fwd_messages']:
                tMessage.fwd_messages.append(RecirsionFwd(fwd))
        try:
            tMessage.chat_id = message['chat_id'] + 2000000000
            tMessage.chat_active = message['chat_active']
            tMessage.users_count = message['users_count']
            tMessage.admin_id = message['admin_id']
            tMessage.isChat = True
        except:
            tMessage.chat_id = message['user_id']
            tMessage.chat_active = [message['user_id']]
            tMessage.admin_id = message['user_id']
            tMessage.users_count = 1
        if 'action' in message:
            tAction = action()

            tAction.action = message['action']
            if tAction.action == tAction.types.chat_title_update:
                tAction.action_text = message['action_text']
            if tAction.action == tAction.types.chat_invite_user:
                tAction.action_mid = message['action_mid']
            if tAction.action == tAction.types.chat_kick_user:
                tAction.action_mid = message['action_mid']
            tMessage.action = tAction
            tMessage.hasAction = True

        a.messages.append(tMessage)
        for Userprofile in resp['profiles']:
            tProfile = profile()
            tProfile.id = Userprofile['id']
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
        try:
            for c in resp['chats']:
                tChat = chat()
                tChat.id = c['id']
                tChat.type = c['type']
                tChat.title = c['title']
                tChat.admin_id = c['admin_id']
                tChat.users = c['users']
                a.chats.append(tChat)
        except:
            a.chats = []
    return a
