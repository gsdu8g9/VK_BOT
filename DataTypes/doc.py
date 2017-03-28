class doc:
    class DocTypes:
        text = 1
        archive = 2
        gif = 3
        img = 4
        audio = 5
        video = 6
        Ebook = 7
        unknown = 8

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
        @staticmethod
        def getType(id):
            vars_ = vars(doc.DocTypes)
            for var in vars_:
                if vars_[var] == id:
                    return var
            else:
                return 'unknown'
