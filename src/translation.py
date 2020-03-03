import gettext
from locale import getdefaultlocale


class Translation:
    @staticmethod
    def temporary_(message):
        return message

    def __init__(self):
        self.gettext = self.temporary_

    def set_lang(self, clp, args):
        current_locale, encoding = getdefaultlocale()
        lang = ''
        if args.lang in clp.all_lang:
            lang = clp.args.lang
        chosen_lang = gettext.translation('DR-Altimeter',
                                          localedir=clp.localedir,
                                          languages=[lang, current_locale],
                                          fallback=True)
        chosen_lang.install()
        self.gettext = chosen_lang.gettext
