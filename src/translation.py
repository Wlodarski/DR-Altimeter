#! python3
"""
MIT License

Copyright (c) 2020 Walter Wlodarski

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import gettext
from locale import getdefaultlocale


class Translation:
    __slots__ = ["gettext"]

    @staticmethod
    def temporary_(message):
        return message

    def __init__(self):
        self.gettext = self.temporary_

    def __call__(self, text):
        return self.gettext(text)

    def set_lang(self, clp):
        current_locale, encoding = getdefaultlocale()
        lang = clp.args.lang if clp.args.lang in clp.all_lang else ""
        chosen_lang = gettext.translation(
            "DR-Altimeter", localedir=clp.localedir, languages=[lang, current_locale], fallback=True,
        )
        chosen_lang.install()
        self.gettext = chosen_lang.gettext
        return self.gettext
