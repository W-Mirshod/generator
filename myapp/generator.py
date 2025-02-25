import random
import re
from PIL import Image, ImageDraw
import random
import base64
from io import BytesIO


class Generator:
    def __init__(self):
        self.settings = {}
        self.images = []
        self.random_images = []
        self.body_id = ""

    def generate(self):

        white_color= ['white', '#FFFFFF', 'rgb(255, 255, 255)', 'hsl(0,0%,100%)']
        self.settings['color'] = random.choice(white_color)
        white_back_methods = ['head', 'body', 'table', 'tr']
        white_backgrounds_dict = {
            'head': '<html lang="de">\n<head>\n<style>\nbody {{\nbackground-color:{};\n}}\n</style>\n</head>'.format(
                self.settings.get("color", "white")),
            'body': '<body style="background-color:{};">'.format(self.settings.get("color", "white")),
            'table': '<table style="background-color:{};">'.format(self.settings.get("color", "white")),
            'tr': '<tr style="background-color:{};">'.format(self.settings.get("color", "white")),
        }
        change_color_tag = random.choice(white_back_methods)


        lines_head = [
            "<!DOCTYPE html>",
            '<html lang="de">' if change_color_tag != 'head' else white_backgrounds_dict[change_color_tag],
            '<body>' if change_color_tag != 'body' else white_backgrounds_dict[change_color_tag],
            '<table>' if change_color_tag != 'table' else white_backgrounds_dict[change_color_tag],
        ]

        insertNameAtPos = self.settings.get("insertNameAtPos", -1)
        setLinkAtPos = self.settings.get("setLinkAtPos", -1)

        randomNames_raw = self.settings.get("randomNames", "").split("\n")
        randomNames = [e.strip() for e in randomNames_raw if e.strip()]

        lines_table = []

        tr_start = white_backgrounds_dict[change_color_tag] if change_color_tag == 'tr' else '<tr>'

        for i, imageurl in enumerate(self.images):
            rb_pre_count = random.randint(0, 2)
            rb_post_count = random.randint(0, 2)
            rb_offset = 0

            for _ in range(rb_pre_count):
                lines_table.append(
                    tr_start+'<td><img src="{}"></td></tr>'.format(self.random_images[rb_offset % len(self.random_images)]))
                rb_offset += 1

            if i == insertNameAtPos:
                random_name = random.choice(randomNames)
                lines_table.append(
                    tr_start+'<td><h3><a style="font-family:Arial,Tahoma,sans-serif">{}</a></h3></td></tr>'.format(
                        random_name))

            if i == setLinkAtPos:
                lines_table.append(tr_start+'<td><a href="%%URL%%"><img src="{}"></a></td></tr>'.format(imageurl))
            else:
                lines_table.append(tr_start+'<td><img src="{}"></td></tr>'.format(imageurl))

            for _ in range(rb_post_count):
                lines_table.append(
                    tr_start+'<td><img src="{}"></td></tr>'.format(self.random_images[rb_offset % len(self.random_images)]))
                rb_offset += 1

        lines_end = [
            '</table>',
            '</body>',
            '</html>'
        ]

        lines = lines_head + lines_table + lines_end

        insert_random_tags = ["body", "table", "tr", "td", "h1"]
        lines_random = []

        for line in lines:
            for tag in insert_random_tags:
                if tag != change_color_tag:
                    search = '<' + tag + '>'
                    if tag in line:
                        if tag == "body" and self.body_id:
                            line = line.replace(search, '<{}{}>'.format(tag, self.random_tags(self.body_id)))
                        else:
                            line = line.replace(search, '<{}{}>'.format(tag, self.random_tags()))
                else:
                    search = '<' + tag + ' style'
                    if tag in line:
                        if tag == "body" and self.body_id:
                            line = line.replace(search, '<{}{} style'.format(tag, self.random_tags(self.body_id)))
                        else:
                            line = line.replace(search, '<{}{} style'.format(tag, self.random_tags()))

            lines_random.append(line)

        separator = "\n" if self.settings.get("use_newlines", 0) == 1 else ""

        return separator.join(lines_random)

    def random_tags(self, force_id=None):
        id_flag = True
        class_flag = True
        name_flag = True

        id_min, id_max = 6, 12
        class_min, class_max = 6, 12
        name_min, name_max = 6, 12

        random_attrs = []

        if id_flag:
            random_attrs.append('id="{}"'.format(self.random_string(random.randint(id_min, id_max))))

        if class_flag:
            random_attrs.append('class="{}"'.format(self.random_string(random.randint(class_min, class_max))))

        if name_flag:
            random_attrs.append('name="{}"'.format(self.random_string(random.randint(name_min, name_max))))

        return " " + " ".join(random_attrs)

    @staticmethod
    def random_string(length):
        characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
        return ''.join(random.choice(characters) for i in range(length))

    def generate_random_by_regex(regex):
        # Словарь для шаблонов и соответствующих им символов
        pattern_map = {
            '\\d': '0123456789',
            '\\w': 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_',
            '\\U': 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        }

        result = ''
        i = 0
        while i < len(regex):
            if regex[i:i + 2] in pattern_map:
                chars = pattern_map[regex[i:i + 2]]
                if i + 2 < len(regex) and regex[i + 2] == '{':
                    count_end = regex.find('}', i + 3)
                    count = int(regex[i + 3:count_end])
                    result += ''.join(random.choice(chars) for _ in range(count))
                    i = count_end + 1
                else:
                    result += random.choice(chars)
                    i += 2
            else:
                result += regex[i]
                i += 1

        return result


class ImageRandomize:
    @staticmethod
    def randomize_object(img, amount):
        sizex, sizey = img.size

        pixels = img.load()

        for _ in range(amount):
            x = random.randint(0, sizex - 1)
            y = random.randint(0, sizey - 1)

            r, g, b, a = img.getpixel((x, y))

            r += (-1) ** random.randint(1, 2) * random.randint(0, 8)
            g += (-1) ** random.randint(1, 2) * random.randint(0, 8)
            b += (-1) ** random.randint(1, 2) * random.randint(0, 8)

            r = max(0, min(r, 255))
            g = max(0, min(g, 255))
            b = max(0, min(b, 255))

            pixels[x, y] = (r, g, b, a)

        return img

    @staticmethod
    def random_blank_in_memory(width, height, randomize=False, random_amount=16):
        img = Image.new('RGBA', (width, height), (255, 255, 255, 255))

        if randomize:
            ImageRandomize.randomize_object(img, random_amount)

        buffer = BytesIO()
        img.save(buffer, format="PNG")

        return 'data:image/png;base64,' + base64.b64encode(buffer.getvalue()).decode()
        # return buffer.getvalue()

    @staticmethod
    def random_blank(file, width, height, randomize=False, random_amount=16):
        img = Image.new('RGBA', (width, height), (255, 255, 255, 255))

        if randomize:
            ImageRandomize.randomize_object(img, random_amount)

        img.save(file, format="PNG")

    @staticmethod
    def randomize(path, amount, outputpath):
        img = Image.open(path).convert('RGBA')

        ImageRandomize.randomize_object(img, amount)

        img.save(outputpath, 'PNG')

    @staticmethod
    def randomize_base64(path, amount):
        img = Image.open(path).convert('RGBA')

        ImageRandomize.randomize_object(img, amount)

        buffer = BytesIO()
        img.save(buffer, format="PNG")

        return 'data:image/png;base64,' + base64.b64encode(buffer.getvalue()).decode()


if __name__ == "__main__":
    print(Generator.generate_random_by_regex(r'ABC\d{6}\w'))
    # for i in range(10):
    #    ImageRandomize.randomize("1.png", 50, f"output{i}.png")

    # img_data = ImageRandomize.random_blank_in_memory(100, 100, True, 50)
    # with open(f"random_image{i}.png", "wb") as f:
    #    f.write(img_data)

    # Create an instance of the Generator class
    gen = Generator()

    # Set up some settings
    gen.settings = {
        "insertNameAtPos": 1,
        "setLinkAtPos": 2,
        "randomNames": "John\nDoe\nSmith",
        "use_newlines": 1
    }

    # Some mock images for demonstration purposes
    gen.images = ["image1.png", "image2.png", "image3.png"]
    gen.random_images = ["random1.png", "random2.png"]

    # Generate the HTML
    html_output = gen.generate()

    # Print or save the HTML
    print(html_output)
