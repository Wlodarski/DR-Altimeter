import gettext
from locale import getdefaultlocale


class Translation:
    @staticmethod
    def temporary_(message):
        return message

    def __init__(self):
        self.gettext = self.temporary_

    def __call__(self, text):
        return self.gettext(text)

    def set_lang(self, clp):
        current_locale, encoding = getdefaultlocale()
        lang = ''
        if clp.args.lang in clp.all_lang:
            lang = clp.args.lang
        chosen_lang = gettext.translation('DR-Altimeter',
                                          localedir=clp.localedir,
                                          languages=[lang, current_locale],
                                          fallback=True)
        chosen_lang.install()
        self.gettext = chosen_lang.gettext
        return self.gettext
