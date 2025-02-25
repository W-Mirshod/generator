import random
import copy
import re
import colorsys
import json
import os

from .generator import ImageRandomize



randstyles = '''    color: %%COLOR%%;
    font-size: %%RANDINT1%%em;
    font-weight: bold;
    text-shadow: %%RANDINT1%%px %%RANDINT2%%px %%RANDINT1%%px %%COLOR%%;
    font-size: %%RANDINT1%%px;
    line-height: %%RANDINT1%%;
    margin: %%RANDINT1%%px %%RANDINT2%%;
    text-decoration: none;
    transition: color %%RANDINT1%%s ease;
    list-style-type: square;
    padding-left: %%RANDINT1%%px;
    margin-bottom: %%RANDINT1%%px;
    display: inline-block;
    padding: %%RANDINT1%%px %%RANDINT1%%px;
    background-color: %%COLOR%%;
    border-radius: %%RANDINT1%%px;
    transition: background-color %%RANDINT1%%s ease;
    background-color: %%COLOR%%;
    flex-direction: row;
    justify-content: space-between;
    border: none;
    width: %%RANDINT1%%%;
    word-break: break-all;
    white-space: pre-wrap;
    border-color: %%COLOR%%;
    min-width: fit-content;
    text-align: center;
    text-decoration: none;
    cursor: pointer;
    height: %%RANDINT1%%px;
    resize: none;
    pointer-events: none;'''.split("\n")

if not "subs.txt" in os.listdir():
    file = open("n0kovo_subdomains_small.txt")
    sub_random = [i if not 'mail' in i else None for i in file.read().split('\n')]
    file.close()
    while None in sub_random:
        sub_random.remove(None)
    file = open("subs.txt", "w")
    file.write(json.dumps(sub_random))
    file.close()
else:
    file = open("subs.txt")
    sub_random = json.loads(file.read())
    file.close()

class Generator:
    def __init__(self, settings, rp):
        self.settings = {}
        for k, v in settings.items():
            self.settings[k] = v[0]

        self.RandPic = rp

    @staticmethod
    def random_string(length):
        characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
        return ''.join(random.choice(characters) for i in range(length))


    @staticmethod
    def macros(input_string):
        pattern = r'\(([^)]+)\)'

        def choose_random_word(match):
            options = match.group(1).split('|')
            return random.choice(options)

        result = re.sub(pattern, choose_random_word, input_string)
        return result



    def generator(self, images_=[], domain=None, link_=None):
        margins = ''
        if int(self.settings["random_maxspaces_left"]) > 0:
            margins += f'margin-left: {random.randint(0,int(self.settings["random_maxspaces_left"]))}px;'
        if int(self.settings["random_maxspaces_top"]) > 0:
            margins += f'margin-top: {random.randint(0,int(self.settings["random_maxspaces_top"]))}px;'
        if int(self.settings["random_maxspaces_bottom"]) > 0:
            margins += f'margin-bottom: {random.randint(0,int(self.settings["random_maxspaces_bottom"]))}px;'
        if int(self.settings["random_maxspaces_right"]) > 0:
            margins += f'margin-right: {random.randint(0,int(self.settings["random_maxspaces_right"]))}px;'

        lines_head = [
            "<!DOCTYPE html>",
            random.choice(['<html lang="de">','<html lang="DE">','<html lang="EN">','<html lang="en">','<html>']) if 1 == int(self.settings['random_html']) else '<html lang="de">',
            f'<body {self.tags()}>',
            f'''<style>\n{Generator.random_styles()}\n</style>''' if 1 == int(self.settings["random_styles"]) else None,
            f'''<table {self.tags(None if len(margins) == 0 else f'style="{margins}"')}>''',
        ]
        while None in lines_head:
            lines_head.remove(None)

        images = list(images_)

        names = [i if len(i) > 2 else None for i in self.settings['randomNames'].replace("\r\n", "\n").split("\n")]
        while None in names:
            names.remove(None)

        lines = []

        src_method = []
        if 1 == int(self.settings['pic_base64']): src_method.append('base64')
        if 1 == int(self.settings['pic_domains']): src_method.append('domain')

        if len(src_method) == 0: src_method.append('base64')

        src_rb_method = []
        if 1 == int(self.settings['rb_base64']): src_rb_method.append('base64')
        if 1 == int(self.settings['rb_domains']): src_rb_method.append('domain')

        if len(src_rb_method) == 0: src_rb_method.append('base64')


        rb_method = []
        if 1 == int(self.settings['rb_randomize']): rb_method.append('rb_randomize')
        if 1 == int(self.settings['rb_use_white_text']): rb_method.append('rb_use_white_text')
        if 1 == int(self.settings['random_whitespaces']): rb_method.append('random_whitespaces')
        if link_ == None:
            link_a = '%%URL%%'
        else:
            link_a = link_.get_link(self.settings['link'])


        for i in range(100):
            if len(images) == 0:
                break
        
            link = i == int(self.settings['setLinkAtPos'])

            if i == int(self.settings['insertNameAtPos']):
                # print("name")
                fonts = ['Arial','Tahoma','sans-serif']
                random.shuffle(fonts)

                rand_h = random.choice(['h1','h2','h3'])

                if link:
                    lines.append(f'''<tr {self.tags()}><td {self.tags()}><{rand_h} {self.tags('style="font-family:'+','.join(fonts)+';color: '+Generator.random_color("black")+'"')}><a {self.tags('href="'+link_a+'" target="'+self.settings['target']+'"')}>{random.choice(names)}</a></{rand_h}></td></tr>''')
                else:
                    lines.append(f'''<tr {self.tags()}><td {self.tags()}><{rand_h} {self.tags('style="font-family:'+','.join(fonts)+';color: '+Generator.random_color("black")+'"')}>{Generator.macros(random.choice(names))}</{rand_h}></td></tr>''')
            
            elif len(images) > 0:
                i = images.pop(0)
                if i.picture:
                    if random.choice(src_method) == 'base64':
                        # print("img_base64")
                        src = i.get_random_base64(int(self.settings['randomize_maxchange']))
                    else:
                        # print("img_link")
                        src = i.gen_random_link(domain, int(self.settings['randomize_maxchange']))

                    if link:
                        lines.append(f'''<tr {self.tags()}><td {self.tags()}><a {self.tags('href="'+link_a+'" target="'+self.settings['target']+'"')}><img {self.tags('src="'+src+'"')}></a></td></tr>''')
                    else:
                        lines.append(f'''<tr {self.tags()}><td {self.tags()}><img {self.tags('src="'+src+'"')}></td></tr>''')
                else:
                    if link:
                        lines.append(f'''<tr {self.tags()}><td {self.tags()}><a {self.tags('href="'+link_a+'" target="'+self.settings['target']+'"')}>{i.text}</a></td></tr>''')
                    else:
                        lines.append(f'''<tr {self.tags()}><td {self.tags()}>{Generator.macros(i.text)}</td></tr>''')

        lines_end = [
            '</table>',
            '</body>',
            '</html>'
        ]

        lines_mixed = []
        while len(lines) > 0:
            if random.choice([1,2]) == 1:
                # print("add random block")
                rb = random.choice(rb_method)
                # print(rb)
                if rb == 'rb_randomize':
                    w = int(self.settings['rb_width_base']) + (random.choice([-1,1])*random.randint(0, int(self.settings['rb_width_range'])))
                    h = int(self.settings['rb_height_base']) + (random.choice([-1,1])*random.randint(0, int(self.settings['rb_height_range'])))
                    amount = random.randint(int(self.settings['rb_amount_min']), int(self.settings['rb_amount_max']))
                    if random.choice(src_rb_method) == "base64" or domain is None:
                        src = ImageRandomize.random_blank_in_memory(w,h,True,amount)
                        lines_mixed.append(f'''<tr {self.tags()}><td {self.tags()}><img {self.tags('src="'+src+'"')}></td></tr>''')
                    else:
                        rndpic = self.RandPic.objects.create(sub=domain, name=Generator.random_name()+".png", rb=True, w=w, h=h, amount=amount)
                        href = f"""{'https://' if domain.domain.ssl else 'http://'}{domain.name}.{domain.domain.domain}/{rndpic.name}"""
                        lines_mixed.append(f'''<tr {self.tags()}><td {self.tags()}><img {self.tags('src="'+href+'"')}></td></tr>''')

                elif rb == 'random_whitespaces':
                    lines_mixed.append('\n'*random.randint(1,3))
                elif rb == 'rb_use_white_text':
                    rnd_tag = random.choice(['div', 'h6', 'h5', 'h4', 'b', 'i'])
                    #rnd_rgba = ','.join([str(random.randint(245,255)) for i in range(4)])
                    lines_mixed.append(f'''<tr {self.tags()}><td {self.tags()}><{rnd_tag} {self.tags('style="font-size:'+self.settings['rb_white_text_font_size']+';color: '+Generator.random_color('white')+'"')}>{Generator.random_name()}</{rnd_tag}></td></tr>''')
            else:
                # print("add orig block")
                l = lines.pop(0)
                lines_mixed.append(l)


        res = "\n".join(lines_head+lines_mixed+lines_end)
        file = open("demo.html", 'w')
        file.write(res)
        file.close()
        return res


    def tags(self, tag=None):
        if tag is None:
            l = []
        else:
            l = [tag]
            if tag.startswith('src=') and random.randint(1,2)==1:
                #add alt
                l.append(f'alt="{Generator.random_name()}"')



        tags = ["id", "class", "name"]
        random.shuffle(tags)
        for i in tags[:random.randint(2,3)]:
            l.append(f'{i}="{Generator.random_name() if 1 == int(self.settings["random_names_in_tags"]) else Generator.random_string(random.randint(6,12))}"')
        random.shuffle(l)
        return " ".join(l)

    def random_color(color):
        if color == 'white':
            rgb = [random.randint(245,255) for i in range(3)]
        elif color == 'black':
            rgb = [random.randint(0,20) for i in range(3)]

        a = random.randint(1,3)
        if a == 1:
            return f'rgb({rgb[0]},{rgb[1]},{rgb[2]})'
        elif a == 2:
            return f'rgba({rgb[0]},{rgb[1]},{rgb[2]},{random.randint(240,255)})'
        elif a == 3:
            return '#{:02x}{:02x}{:02x}'. format(rgb[0], rgb[1], rgb[2])
        # elif a == 4:
        #     if color == "white":
        #         return f"hsl({random.randint(0,350)}, {random.randint(0,20)}%, {random.randint(98,100)}%)"
        #     elif color == "black":
        #         return f"hsl({random.randint(0,350)}, {random.randint(0,100)}%, {random.randint(0,7)}%)"

    def random_name(sub=False):
        if sub:
            return random.choice(sub_random)
        j = ['','-'] if sub else ['', '-', '_', ','] 
        file = open("english.txt")
        words = file.read().split('\n')
        file.close()
        r = []
        for i in range(random.randint(2,4 if sub else 9)):
            if random.randint(1,4) == 1:
                r.append(str(random.randint(1,10000)))
            else:
                r.append(random.choice(words))
        return random.choice(j).join(r)


    def random_styles():
        res = []
        for i in range(2,10):
            name = [random.choice(['','#','.'])+Generator.random_name(True)] + [random.choice(['table','h6','tr','td','div','img','p','body']) for i in range(random.randint(0,4))]
            styles = [random.choice(randstyles).replace("%%COLOR%%", Generator.random_color(random.choice(['white','black']))).replace("%%RANDINT1%%",str(random.randint(0,50))).replace("%%RANDINT2%%",str(random.randint(0,50))) for i in range(random.randint(2,10))]
            res.append(" > ".join(name) + ' {'+'\n'.join(styles)+'}')

        h = ("\n\n".join(res)).replace("{    ", "{\n    ").replace(";}",";\n}")
        return h


    def random_subj(self, count=1):
        subj = [i if len(i) > 2 else None for i in self.settings['subjects'].replace("\r\n", "\n").split("\n")]
        r1 = [i if len(i) > 2 else None for i in self.settings['random1'].replace("\r\n", "\n").split("\n")]
        r2 = [i if len(i) > 2 else None for i in self.settings['random2'].replace("\r\n", "\n").split("\n")]
        r3 = [i if len(i) > 2 else None for i in self.settings['random3'].replace("\r\n", "\n").split("\n")]
        while None in subj:
            subj.remove(None)
        while None in r1:
            r1.remove(None)
        while None in r2:
            r2.remove(None)
        while None in r3:
            r3.remove(None)

        if len(r1) == 0: r1.append(r"\d{10}")
        if len(r2) == 0: r2.append(r"\d{10}")
        if len(r3) == 0: r3.append(r"\d{10}")

        return [Generator.generate_random_by_regex(random.choice(subj)).replace("%random1%",Generator.generate_random_by_regex(random.choice(r1))).replace("%random2%",Generator.generate_random_by_regex(random.choice(r2))).replace("%random3%",Generator.generate_random_by_regex(random.choice(r3))) for i in range(count)]
    
    def random_from(self, count=1):
        from_ = [i if len(i) > 2 else None for i in self.settings['from'].replace("\r\n", "\n").split("\n")]
        while None in from_:
            from_.remove(None)

        return [Generator.generate_random_by_regex(random.choice(from_)) for i in range(count)]

    def generate_random_by_regex(regex):
        pattern_map = {
            '\\d': '0123456789',
            '\\w': 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_',
            '\\U': 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        }

        result = ''
        i = 0
        while i < len(regex):
            if regex[i:i+2] in pattern_map:
                chars = pattern_map[regex[i:i+2]]
                if i + 2 < len(regex) and regex[i+2] == '{':
                    count_end = regex.find('}', i+3)
                    count = int(regex[i+3:count_end])
                    result += ''.join(random.choice(chars) for _ in range(count))
                    i = count_end + 1
                else:
                    result += random.choice(chars)
                    i += 2
            else:
                result += regex[i]
                i += 1

        return result

if __name__ == "__main__":
    # print(Generator.random_styles())
    exit()
    default = {
            "insertNameAtPos": [0, False],
            "setLinkAtPos": [1, False],
            "link": ["https://google.com", False],
            
            "rb_randomize": [1, False],
            "rb_width_base": [640, False],
            "rb_width_range": [8, False],
            "rb_height_base": [16, False],
            "rb_height_range": [8, False],
            "rb_amount_min": [16, False],
            "rb_amount_max": [128, False],

            "rb_use_white_text": [0, False],
            "rb_white_text_font_size": ["9pt", False],
            
            "randomize_maxchange": [16, False],
            "pic_base64": [1, False],
            "pic_domains": [0, False],

            "random_whitespaces": [1, False],
            "random_maxspaces_left": [10, False],
            "random_maxspaces_top": [0, False],
            "random_maxspaces_bottom": [0, False],
            "random_maxspaces_right": [0, False],

            "randomNames": ["Sehr geehrte(r) %%NAME%%\nGuten Tag %%NAME%%\n", True],
    }
    g = Generator(default)
    # print(g.tags())
    # print(g.tags(f'href="http://123"'))
    # print(g.generator())
