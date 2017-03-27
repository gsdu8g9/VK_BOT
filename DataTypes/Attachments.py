class Attachment:
    class types:
        photo = 'photo'
        video = 'video'
        audio = 'audio'
        doc = 'doc'
        link = 'link'
        market = 'market'
        market_album = 'market_album'
        wall = 'wall'
        wall_reply = 'wall_reply'
        sticker = 'sticker'
        gift = 'gift'

    class Photo:
        def __init__(self):
            self.id = 0
            self.album_id = 0
            self.owner_id = 0
            self.access_key = ''
            self.photo = ''
        def __str__(self):
            return str(dict({var: str(vars(self)[var]) for var in vars(self)}))

        def AsDict(self):
            return {var: vars(self)[var] for var in vars(self)}

    class Doc:
        class DocTypes:
            text = 1
            archive = 2
            gif = 3
            img = 4
            audio = 5
            video = 6
            Ebook = 7
            unknown = 8
            @staticmethod
            def getType(id):
                vars_ = vars(Attachment.Doc.DocTypes)
                for var in vars_:
                    if vars_[var] == id:
                        return var
                else:
                    return 'unknown'


        def __init__(self):
            self.id = 0
            self.owner_id = 0
            self.title = ''
            self.size = 0
            self.ext = ''
            self.url = ''
            self.date = 0
            self.type = ''
            self.url = ''
            self.url = ''

    def __init__(self):
        self.type = ''
        self.photo = None
        self.video = None
        self.audio = None
        self.doc = None
        self.link = None
        self.market = None
        self.market_album = None
        self.wall = None
        self.wall_reply = None
        self.sticker = None
        self.gift = None
    def __str__(self):
        return str(dict({var: str(vars(self)[var]) for var in vars(self)}))

    def AsDict(self):
        return {var: vars(self)[var] for var in vars(self)}