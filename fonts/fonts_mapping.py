import os

from PIL import Image, ImageFont, ImageDraw, ImageOps


class Icon:
    default_colour = ('', (0, 0, 0))

    def __init__(self, letter):
        try:
            self.letter = letter.letter
            self.colours = letter.colours
            self.size = letter.size
        except AttributeError:
            self.letter = letter
            self.colours = [self.default_colour]
            self.size = 128

    @staticmethod
    def factory(name=None, colour=None, size=None):
        class Temp(Icon):
            def __init__(self, letter):
                super().__init__(letter)
                if colour and name:
                    self.colours.append((name, colour))
                if size:
                    self.size = size
        return Temp


Red = Icon.factory('red', "#EF232B")
Green = Icon.factory('green', "#6BBE44")
Yellow = Icon.factory('yellow', "#B6B335")
Blue = Icon.factory('blue', "#7ED3E5")
Orange = Icon.factory('orange', "#E5B922")
Purple = Icon.factory('purple', "#B590D3")

Medium = Icon.factory(size=100)


fonts = {
    "xwing-miniatures-ships.ttf": {
        "asf01bwing": "b",
        "arc170starfighter": "c",
        "attackshuttle": "g",
        "auzituckgunship": "@",
        "btla4ywing": "y",
        "btls8kwing": "k",
        "ewing": "e",
        "fangfighter": "M",
        "hwk290lightfreighter": "h",
        "modifiedyt1300lightfreighter": "m",
        "rz1awing": "a",
        "sheathipedeclassshuttle": "%",
        "t65xwing": "x",
        "ut60duwing": "u",
        "vcx100lightfreighter": "G",
        "yt2400lightfreighter": "o",
        "yt2400lightfreighter2023": "o",
        "z95af4headhunter": "z",
        "aggressorassaultfighter": "i",
        "jumpmaster5000": "p",
        "kihraxzfighter": "r",
        "lancerclasspursuitcraft": "L",
        "m12lkimogilafighter": "K",
        "m3ainterceptor": "s",
        "modifiedtielnfighter": "C",
        "quadrijettransferspacetug": "q",
        "rogueclassstarfighter": "|",
        "scurrgh6bomber": "H",
        "st70assaultship": "'",
        "starviperclassattackplatform": "v",
        "tridentclassassaultship": "7",
        "yv666lightfreighter": "t",
        "customizedyt1300lightfreighter": "W",
        "escapecraft": "X",
        "g1astarfighter": "n",
        "alphaclassstarwing": "&",
        "gauntletfighter": "6",
        "gozanticlasscruiser": "4",
        "lambdaclasst4ashuttle": "l",
        "raiderclasscorvette": "3",
        "tieadvancedv1": "R",
        "tieadvancedx1": "A",
        "tieininterceptor": "I",
        "tiereaper": "V",
        "tieddefender": "D",
        "tieagaggressor": "`",
        "tiecapunisher": "N",
        "tielnfighter": "F",
        "tiephphantom": "P",
        "tiesabomber": "B",
        "tieskstriker": "T",
        "vt49decimator": "d",
        "tierbheavy": "J",
        "gr75mediumtransport": "1",
        "mg100starfortresssf17": "Z",
        "scavengedyt1300": "Y",
        "rz2awing": "E",
        "t70xwing": "w",
        "resistancetransport": ">",
        "resistancetransportpod": "?",
        "fireball": "0",
        "btanr2ywing": "{",
        "tiebainterceptor": "j",
        "tiefofighter": "O",
        "tiesffighter": "S",
        "tievnsilencer": "$",
        "upsilonclasscommandshuttle": "U",
        "xiclasslightshuttle": "Q",
        "tiesebomber": "!",
        "tiewiwhispermodifiedinterceptor": "#",
        "vultureclassdroidfighter": "_",
        "croccruiser": "5",
        "belbullab22starfighter": "[",
        "sithinfiltrator": "]",
        "hyenaclassdroidbomber": "=",
        "nantexclassstarfighter": ";",
        "droidtrifighter": "+",
        "hmpdroidgunship": ".",
        "firesprayclasspatrolcraft": "f",
        "delta7aethersprite": "\\",
        "cr90corelliancorvette": "2",
        "v19torrentstarfighter": "^",
        "nabooroyaln1starfighter": "<",
        "btlbywing": ":",
        "eta2actis": "-",
        "laatigunship": "/",
        "nimbusclassvwing": ",",
        "syliureclasshyperspacering": "*",
        "clonez95headhunter": "}"
    }
}


size = (128, 128)


def main():
    if not os.path.exists('emoji'):
        os.mkdir('emoji')

    for font, glyphs in fonts.items():
        for name, glyph in glyphs.items():
            try:
                colours = glyph.colours
                glyph = glyph.letter
            except AttributeError:
                colours = [Icon.default_colour]

            fontSize = 130

            if font == "xwing-miniatures-ships.ttf":
                fontSize = 200

            imfont = ImageFont.truetype(font, fontSize)
            for colour_name, colour in colours:
                im = Image.new("RGBA", (300, 300), (255, 255, 255, 0))

                draw = ImageDraw.Draw(im)

                if font == "xwing-miniatures-ships.ttf":
                    draw.arc((75, 75, 225, 225), start=0, end=360, fill="#F2F3F5", width=100)

                draw.text((151, 152), glyph, font=imfont, fill=colour, anchor='mm')

                # remove unneccessory whitespaces if needed
                im = im.crop(ImageOps.invert(im.convert('RGB')).getbbox())

                # im = ImageOps.invert(im)
                im.thumbnail(size, Image.LANCZOS)

                background = Image.new('RGBA', size, (255, 255, 255, 0))

                background.paste(
                    im,
                    ((size[0] - im.size[0]) // 2, (size[1] - im.size[1]) // 2))

                # write into file
                background.save(f"emoji/{colour_name}{name}.png")


if __name__ == '__main__':
    main()
