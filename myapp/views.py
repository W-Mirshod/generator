import json
import re
import os
import random
import io
import logging
import threading
from zipfile import ZipFile
import requests
from typing import Optional, Tuple
from django.conf import settings
from dataclasses import dataclass

from django.shortcuts import render
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.http import FileResponse
from datetime import datetime, timezone, date, timedelta
from django.db import transaction
from .models import *
from .forms import UploadFileForm
from .randomizer import Generator
from .models import schedule_domain_checks

logger = logging.getLogger(__name__)

schedule_domain_checks()

if not "pics" in os.listdir():
    os.mkdir("pics")
if not "logs" in os.listdir():
    os.mkdir("logs")
if not "rand_pics" in os.listdir():
    os.mkdir("rand_pics")

default = {
    "insertNameAtPos": [0, False],
    "setLinkAtPos": [1, False],
    "link": ["https://google.com", False],
    "links_count": [50, False],

    "rb_randomize": [1, False],
    "rb_base64": [1, False],
    "rb_domains": [0, False],
    "rb_width_base": [640, False],
    "rb_width_range": [8, False],
    "rb_height_base": [16, False],
    "rb_height_range": [8, False],
    "rb_amount_min": [16, False],
    "rb_amount_max": [128, False],

    "rb_use_white_text": [1, False],
    "rb_white_text_font_size": ["9pt", False],

    "randomize_maxchange": [16, False],
    "pic_base64": [1, False],
    "pic_domains": [1, False],
    "domains_only_https": [1, False],
    "domains_use_sub": [50, False],

    "random_styles": [1, False],
    "random_alt": [1, False],
    "random_html": [1, False],
    "random_names_in_tags": [1, False],
    "random_whitespaces": [1, False],
    "random_maxspaces_left": [10, False],
    "random_maxspaces_top": [0, False],
    "random_maxspaces_bottom": [0, False],
    "random_maxspaces_right": [0, False],

    "randomNames": ["(Hi|Hello|Guten Tag) %%NAME%%\n", True],
    "subjects": [
        "\\d{14}\nDE\\d{10}\nDE-\\U{2}-\\d{8}\nF-\\d{8}\n[var:2] [var:3] - Eine Unbekannte Transaktion [\\d{10}] wurde auf Ihrem Konto festgestellt! - [%random1%]",
        True],
    "random1": ["Ihre Handlung ist erforderlich!\nREF: PB\\d{10}", True],
    "random2": ["", True],
    "random3": ["", True],
    "from": ["From ABC\\d{12}\n\\U{5}-\\d{10}", True],
    "from_count": [1000, False],
    "subjects_enable": [1, False],
    "subjects_count": [1000, False],
    "bodys_per_subdomain": [5, False],
    "target": ["_self", False],
}
"""
            "randomize_amount": 20,
            "use_newlines": 1,

"""


def evenly_distribute(l1, l2):
    res = []
    l2_index = 0  # Индекс для второго списка
    l2_len = len(l2)

    # Перебор элементов из первого списка
    for i in range(max(len(l1), len(l2))):
        # Добавление пары в результат
        res.append([l1[i % len(l1)], l2[l2_index]])
        l2_index += 1

        # Если мы достигли конца l2, начинаем сначала
        if l2_index >= l2_len:
            l2_index = 0

    return res


def domains_parse(lines):
    res = []
    for i in lines:
        try:
            r = re.search(r'([^@/\n]{1,}\.\w{1,})', i)
            res.append(r.group(0).replace("*.", ""))
        except:
            pass
    return set(res)


def zip_thread(z, s, j):
    try:
        p = Pictures.objects.filter(session=s)
        g = Generator(j['settings'], RandPic)

        # buffer = io.BytesIO()
        # buffer.name = 'result.zip'
        buffer = f'pics/{z.filename}.zip'

        print(evenly_distribute(s.domains.all(), s.links.all()))
        # return

        domains = []
        links = [None]
        if int(j['settings']['pic_domains'][0]) == 1:
            domains = s.domains.all().filter(valid=True)
            if domains.count() == 0:
                return HttpResponse(
                    '<form method="GET"><button type="submit">Return</button></form><hr>No valid domains, check domains or disable "pic_domains".')

            if int(j['settings']['domains_only_https'][0]) == 1:
                domains = domains.filter(ssl=True)
                if domains.count() == 0:
                    return HttpResponse(
                        '<form method="GET"><button type="submit">Return</button></form><hr>No valid domains with <b>SSL</b>, create ssl for domains or disable "domains_only_https".')

            links = s.links.all().filter(valid=True)
            if links.count() == 0:
                links = [None]
                # return HttpResponse('<form method="GET"><button type="submit">Return</button></form><hr>No valid domains for link, check domains or disable "pic_domains".')
            else:
                if int(j['settings']['domains_only_https'][0]) == 1:
                    links = links.filter(ssl=True)
                    if links.count() == 0:
                        links = [None]
                        # return HttpResponse('<form method="GET"><button type="submit">Return</button></form><hr>No valid domains with <b>SSL</b>, create ssl for domains or disable "domains_only_https".')

            domains_done = []
            with ZipFile(buffer, 'a') as zip_file:
                # for dom_ in domains:
                for doms_ in evenly_distribute(domains, links):
                    print(doms_)
                    dom_ = doms_[0]
                    if dom_ in domains_done:
                        continue
                    else:
                        domains_done.append(dom_)
                    lnk_ = doms_[1]
                    link_ = random.choice(doms_[1].get_sub()) if doms_[1].ssl else Sub.objects.create(domain=doms_[1],
                                                                                                      name=Generator.random_name(
                                                                                                          True))
                    dom_.used = True
                    dom_.save()
                    lnk_.used = True
                    lnk_.save()
                    subs = list(dom_.get_sub())
                    if len(subs) > int(j['settings']['domains_use_sub'][0]):
                        subs = subs[:int(j['settings']['domains_use_sub'][0])]
                    for sub_ in subs:
                        for i in range(int(j['settings']['bodys_per_subdomain'][0])):
                            subj = ''
                            if int(j['settings']['domains_only_https'][0]) == 1:
                                subj_ = '\n'.join(
                                    [s + "<br>" for s in g.random_subj(int(j['settings']['subjects_count'][0]))])
                                from_ = '\n'.join(
                                    [s + "<br>" for s in g.random_from(int(j['settings']['from_count'][0]))])
                                links_ = '\n'.join(
                                    [link_.get_link(random.choice(j['settings']['link'][0].split("|"))) + "<br>" for s
                                     in range(int(j['settings']['links_count'][0]))])
                                subj = f'Subjects:<br>\n{subj_}\n<br>From:<br>\n{from_}\n<br>Link4 or Short:<br>\n{links_}\n\n'
                            zip_file.writestr(f'{sub_.name}.{dom_.domain}-body{i + 1}.html',
                                              subj + g.generator(p, sub_, None))

        else:
            with ZipFile(buffer, 'a') as zip_file:
                for i in range(int(j['settings']['bodys_per_subdomain'][0])):
                    subj = ''
                    if int(j['settings']['domains_only_https'][0]) == 1:
                        subj_ = '\n'.join([s + "<br>" for s in g.random_subj(int(j['settings']['subjects_count'][0]))])
                        from_ = '\n'.join([s + "<br>" for s in g.random_from(int(j['settings']['from_count'][0]))])
                        # subj = f'Subjects:<br>\n{subj_}\n<br>Link4 or Short:<br>\n\n'
                        subj = f'Subjects:<br>\n{subj_}\n<br>From:<br>\n{from_}\n<br>Link4 or Short:<br>\n\n'
                    zip_file.writestr(f'base64-body{i + 1}.html', subj + g.generator(p, None, None))
        # buffer.seek(0)
        # return FileResponse(buffer)
    except:
        z.error_text = format_exc()
        z.error = True
    finally:
        z.done = True
        z.save()


# # for swapping old domains
# logger = logging.getLogger(__name__)

# def check_domain_status(domain):
#     """Checks the status of a domain using requests.  Includes error handling and logging."""
#     try:
#         response = requests.get(f'http://subdomaintest.{domain.domain}/teeeeeeeeeeeest/', timeout=3)
#         response.raise_for_status()
#         return True
#     except requests.exceptions.RequestException as e:
#         logger.error(f"Error checking domain {domain.domain}: {e}")
#         return False


# def swap_domain(domain):
#     """Swaps a down domain, updating references."""
#     available_hold_domains = DomainsHold.objects.filter(domain__status='hold')
#     if available_hold_domains.exists():
#         replacement_domain = available_hold_domains.first().domain
#         try:
#             with transaction.atomic():
#                 domain.status = 'hold'
#                 domain.save()
#                 replacement_domain.status = 'in_use'
#                 replacement_domain.save()
#                 Domains.objects.filter(domain=domain).update(domain=replacement_domain)
#                 logger.info(f"Swapped domain {domain.domain} with {replacement_domain.domain}")
#             return replacement_domain
#         except Exception as e:
#             logger.exception(f"Error swapping domain {domain.domain}: {e}")
#             return None
#     else:
#         logger.warning(f"No replacement domain found for {domain.domain}")
#         return None


# def check_and_swap_domains():
#     for domain in Domains.objects.filter(status='in_use'):
#         if not check_domain_status(domain):
#             swapped_domain = swap_domain(domain)
#             if swapped_domain is None:
#                 logger.error(f"Failed to swap domain {domain.domain}. No replacement found or error during swap.")


# Create your views here.
def admin(request):
    if request.method == "POST":
        print(request.POST)

    if request.method == "POST" and "create_session" in request.POST:
        print("create new session")
        s, created = Sessions.objects.get_or_create(name=request.POST['session_name'])
        if created:
            s.settings = json.dumps(default)
            s.save()
        request.session['session'] = s.id

    elif request.method == "POST" and "delete_session" in request.POST:
        Sessions.objects.get(id=request.POST['delete_session']).delete()
        if "session" in request.session and request.session["session"] == int(request.POST['delete_session']):
            del request.session['session']

    elif request.method == "POST" and "select_session" in request.POST:
        s = Sessions.objects.get(id=request.POST['select_session'])
        request.session['session'] = s.id

    if not "session" in request.session:
        j = {'sessions': Sessions.objects.all()}
        return render(request, "index.html", j)
    s = Sessions.objects.get(id=request.session['session'])
    j = {'sessions': Sessions.objects.all(), "session_selected": s, 'settings': json.loads(s.settings)}

    # print(request.FILES)
    if request.method == 'POST':
        if 'file' in request.FILES and "addimage" in request.POST:
            form = UploadFileForm(request.POST, request.FILES)
            if form.is_valid():
                print("valid")
                uploaded_file = request.FILES['file']
                file_bytes = uploaded_file.read()
                # print(file_bytes)
                new_id = str(Pictures.objects.filter(session=s).count() + 1)
                p = Pictures(session=s, name=new_id)
                p.save()
                file = open(f'pics/{p.filename}', 'wb')
                file.write(file_bytes)
                file.close()
                p.set_extension()
            else:
                print("not valid")

        elif "addtext" in request.POST:
            p, c = Pictures.objects.get_or_create(session=s, text=request.POST.get("text", None), picture=False)

        elif 'file' in request.FILES and "adddomains" in request.POST:
            form = UploadFileForm(request.POST, request.FILES)
            if form.is_valid():
                print("valid")
                uploaded_file = request.FILES['file']
                lines = uploaded_file.read().decode().split("\n")
                domains = domains_parse(lines)
                print(domains)
                for i in domains:
                    d, created = Domains.objects.get_or_create(domain=i)
                    # if not d in s.domains.all():
                    if not d in s.links.all() and not d in s.domains.all():
                        s.domains.add(d)
            else:
                print("not valid")

        elif 'file' in request.FILES and "addlinks" in request.POST:
            form = UploadFileForm(request.POST, request.FILES)
            if form.is_valid():
                print("valid")
                uploaded_file = request.FILES['file']
                lines = uploaded_file.read().decode().split("\n")
                domains = domains_parse(lines)
                print(domains)
                for i in domains:
                    d, created = Domains.objects.get_or_create(domain=i)
                    if not d in s.links.all() and not d in s.domains.all():
                        s.links.add(d)
            else:
                print("not valid")

        elif "delimage" in request.POST:
            Pictures.objects.get(id=request.POST["delimage"]).delete()

        elif "deldomain" in request.POST:
            if request.POST["deldomain"] == 'all':
                [s.domains.remove(d) for d in s.domains.all()]
            else:
                d = Domains.objects.get(id=request.POST["deldomain"])
                print(d)
                print(s.domains.all())
                s.domains.remove(d)

        elif "dellink" in request.POST:
            if request.POST["dellink"] == 'all':
                [s.links.remove(d) for d in s.links.all()]
            else:
                d = Domains.objects.get(id=request.POST["dellink"])
                print(d)
                s.links.remove(d)

        elif "setsettings" in request.POST:
            for key in request.POST.keys():
                if not key in ['setsettings', 'csrfmiddlewaretoken']:
                    value = request.POST.get(key)
                    j['settings'][key][0] = value

            s.settings = json.dumps(j['settings'])
            s.save()

        elif "generate" in request.POST:
            p = Pictures.objects.filter(session=s)
            j['settings']['pic_domains'][0] = 0
            g = Generator(j['settings'], RandPic)

            domains = []
            if int(j['settings']['pic_domains'][0]) == 1:
                domains = s.domains.all().filter(valid=True)
                if domains.count() == 0:
                    return HttpResponse(
                        '<form method="GET"><button type="submit">Return</button></form><hr>No valid domains, check domains or disable "pic_domains".')

                if int(j['settings']['domains_only_https'][0]) == 1:
                    domains = domains.filter(ssl=True)
                    if domains.count() == 0:
                        return HttpResponse(
                            '<form method="GET"><button type="submit">Return</button></form><hr>No valid domains with <b>SSL</b>, create ssl for domains or disable "domains_only_https".')

            r = g.generator(p, random.choice(random.choice(list(domains)).get_sub()) if int(
                j['settings']['pic_domains'][0]) == 1 else None)
            return HttpResponse('<form method="GET"><button type="submit">Return</button></form><hr>' + r)

        elif "zip" in request.POST:
            z = Zips.objects.create(session=s)
            z.save()

            threading.Thread(target=zip_thread, args=(z, s, j), daemon=True).start()

            return HttpResponseRedirect("?")
            # p = Pictures.objects.filter(session=s)
            # g = Generator(j['settings'])

            # buffer = io.BytesIO()
            # buffer.name = 'result.zip'

            # print(evenly_distribute(s.domains.all(),s.links.all()))
            # #return

            # domains = []
            # links = [None]
            # if int(j['settings']['pic_domains'][0]) == 1:
            #     domains = s.domains.all().filter(valid=True)
            #     if domains.count() == 0:
            #         return HttpResponse('<form method="GET"><button type="submit">Return</button></form><hr>No valid domains, check domains or disable "pic_domains".')

            #     if int(j['settings']['domains_only_https'][0]) == 1:
            #         domains = domains.filter(ssl=True)
            #         if domains.count() == 0:
            #             return HttpResponse('<form method="GET"><button type="submit">Return</button></form><hr>No valid domains with <b>SSL</b>, create ssl for domains or disable "domains_only_https".')

            #     links = s.links.all().filter(valid=True)
            #     if links.count() == 0:
            #         links = [None]
            #         #return HttpResponse('<form method="GET"><button type="submit">Return</button></form><hr>No valid domains for link, check domains or disable "pic_domains".')
            #     else:
            #         if int(j['settings']['domains_only_https'][0]) == 1:
            #             links = links.filter(ssl=True)
            #             if links.count() == 0:
            #                 links = [None]  
            #                 #return HttpResponse('<form method="GET"><button type="submit">Return</button></form><hr>No valid domains with <b>SSL</b>, create ssl for domains or disable "domains_only_https".')

            #     domains_done = []
            #     with ZipFile(buffer, 'a') as zip_file:
            #         #for dom_ in domains:
            #         for doms_ in evenly_distribute(domains,links):
            #             print(doms_)
            #             dom_ = doms_[0]
            #             if dom_ in domains_done:
            #                 continue
            #             else:
            #                 domains_done.append(dom_)
            #             lnk_ = doms_[1]
            #             link_ = random.choice(doms_[1].get_sub()) if doms_[1].ssl else Sub.objects.create(domain=doms_[1],name=Generator.random_name(True))
            #             dom_.used = True 
            #             dom_.save()
            #             lnk_.used = True 
            #             lnk_.save()                        
            #             subs = list(dom_.get_sub())
            #             if len(subs) > int(j['settings']['domains_use_sub'][0]):
            #                 subs = subs[:int(j['settings']['domains_use_sub'][0])]
            #             for sub_ in subs:
            #                 for i in range(int(j['settings']['bodys_per_subdomain'][0])):
            #                     subj = ''
            #                     if int(j['settings']['domains_only_https'][0]) == 1:
            #                         subj_ = '\n'.join([s+"<br>" for s in g.random_subj(int(j['settings']['subjects_count'][0]))])
            #                         from_ = '\n'.join([s+"<br>" for s in g.random_from(int(j['settings']['from_count'][0]))])
            #                         links_ = '\n'.join([link_.get_link(j['settings']['link'][0])+"<br>" for s in range(int(j['settings']['links_count'][0]))])
            #                         subj = f'Subjects:<br>\n{subj_}\n<br>From:<br>\n{from_}\n<br>Link4 or Short:<br>\n{links_}\n\n'
            #                     zip_file.writestr(f'{sub_.name}.{dom_.domain}-body{i+1}.html', subj+g.generator(p, sub_, None))

            # else:
            #     with ZipFile(buffer, 'a') as zip_file:
            #         for i in range(int(j['settings']['bodys_per_subdomain'][0])):
            #             subj = ''
            #             if int(j['settings']['domains_only_https'][0]) == 1:
            #                 subj_ = '\n'.join([s+"<br>" for s in g.random_subj(int(j['settings']['subjects_count'][0]))])
            #                 from_ = '\n'.join([s+"<br>" for s in g.random_from(int(j['settings']['from_count'][0]))])
            #                 #subj = f'Subjects:<br>\n{subj_}\n<br>Link4 or Short:<br>\n\n'
            #                 subj = f'Subjects:<br>\n{subj_}\n<br>From:<br>\n{from_}\n<br>Link4 or Short:<br>\n\n'
            #             zip_file.writestr(f'base64-body{i+1}.html', subj+g.generator(p, None, None))

            # buffer.seek(0)
            # return FileResponse(buffer)
            # r = g.generator(p, random.choice(list(domains)))
            # return HttpResponse('<form method="GET"><button type="submit">Return</button></form><hr>'+r)

        elif request.method == 'POST' and "ssl" in request.POST:
            d = Domains.objects.get(id=request.POST['ssl'])
            d.take_ssl(int(j['settings']['domains_use_sub'][0]))

        elif request.method == 'POST' and "reuse" in request.POST:
            d = Domains.objects.get(id=request.POST['reuse'])
            d.used = False
            d.save()

        elif request.method == 'POST' and "checkdomain" in request.POST:
            if request.POST['checkdomain'] == 'all':
                [d.take_check() for d in s.domains.all()]
            else:
                d = Domains.objects.get(id=request.POST['checkdomain'])
                d.take_check()

    if "error" in request.GET:
        d = Domains.objects.get(id=request.GET['error'])
        return HttpResponse(
            '<form method="GET"><button type="submit">Return</button></form><hr>' + str(d.error_text).replace("\n",
                                                                                                              "<br>"))

    if "error_zip" in request.GET:
        d = Zips.objects.get(id=request.GET['error_zip'])
        return HttpResponse(
            '<form method="GET"><button type="submit">Return</button></form><hr>' + str(d.error_text).replace("\n",
                                                                                                              "<br>"))

    if "sublist" in request.GET:
        d = Domains.objects.get(id=request.GET['sublist'])
        return HttpResponse('<form method="GET"><button type="submit">Return</button></form><hr>' + "<br>".join(
            [f'<a href="{i.get_test()}/teeeeeeeeeeeest/">{i.get_test()}</a>' for i in d.get_sub()]))

    print(j)
    return render(request, "index.html", j)


def get_picture(request, resource):
    resource = resource.replace('pics_reger/', '')
    
    try:
        picture = Pictures.objects.get(filename=resource)
        return FileResponse(open(f'pics/{picture.filename}', 'rb'))
    except Pictures.DoesNotExist:
        try:
            randpic = RandPic.objects.get(name=resource)
            randpic.check_file()
            return FileResponse(open(f'rand_pics/{randpic.filename}.png', 'rb'))
        except RandPic.DoesNotExist:
            try:
                randlink = RandLink.objects.get(link=resource)
                RedirectCounter.objects.get_or_create(link=randlink)[0].increment()
                return HttpResponseRedirect(randlink.origlink)
            except RandLink.DoesNotExist:
                return HttpResponse(status=404)


def antired(request):
    if request.method == "POST":
        r = request.POST.get("key")
        n = request.POST.get("value")
        action = request.POST.get("action")
        if action == "update":
            for i in RandLink.objects.filter(origlink=r):
                i.origlink = n
                i.save()
        elif action == "delete":
            RandLink.objects.filter(origlink=r).delete()
        elif action == "add":
            if n:  # Ensure that the new link value is not empty
                antired_sub = Sub.objects.first()
                new_link = RandLink(origlink=n,
                                    link=Generator.random_name() + random.choice(['.php', '.html', '.htm', '.asp', '']),
                                    sub=antired_sub)
                new_link.save()
    links = list(RandLink.objects.all().values_list('origlink', flat=True).distinct())
    return render(request, "antired.html", {"links": links})


@dataclass
class TelegramCheck:
    is_listed: bool
    can_enable: bool
    error: Optional[str] = None


class TelegramDomainChecker:
    def __init__(self, api_token: str):
        self.api_token = api_token
        self.base_url = f"https://api.telegram.org/bot{api_token}"

    def check_domain(self, domain: str) -> TelegramCheck:
        try:
            check_url = f"{self.base_url}/checkWebhook"
            params = {"url": f"https://{domain}/test"}

            response = requests.get(check_url, params=params, timeout=(5, 15))
            response.raise_for_status()
            data = response.json()

            if not data.get("ok"):
                return TelegramCheck(
                    is_listed=False,
                    can_enable=False,
                    error=data.get("description", "Unknown error checking domain"))

            can_enable = "ok" in data and not data.get("result", {}).get("has_custom_certificate", False)

            return TelegramCheck(
                is_listed=True,
                can_enable=can_enable)
        except requests.RequestException as e:
            logger.error(f"Error checking domain {domain} with Telegram: {str(e)}")
            return TelegramCheck(
                is_listed=False,
                can_enable=False,
                error=f"Request failed: {str(e)}")

    def enable_domain(self, domain: str) -> Tuple[bool, Optional[str]]:
        try:
            check_result = self.check_domain(domain)
            if not check_result.can_enable:
                return False, "Domain cannot be enabled"

            enable_url = f"{self.base_url}/setWebhook"
            params = {
                "url": f"https://{domain}/webhook",
                "allowed_updates": ["message", "callback_query"],
                "drop_pending_updates": True}

            response = requests.post(enable_url, json=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("ok"):
                return True, None
            else:
                return False, data.get("description", "Unknown error enabling domain")

        except requests.RequestException as e:
            error_msg = f"Error enabling domain {domain}: {str(e)}"
            logger.error(error_msg)
            return False, error_msg


def check_telegram_status(self):
    checker = TelegramDomainChecker(settings.TELEGRAM_BOT_TOKEN)
    result = checker.check_domain(self.domain)

    self.telegram_listed = result.is_listed
    self.telegram_last_checked = timezone.now()
    self.telegram_error = result.error

    if result.is_listed and result.can_enable and settings.TELEGRAM_AUTO_ENABLE:
        success, error = checker.enable_domain(self.domain)
        self.telegram_enabled = success
        if error:
            self.telegram_error = error

    self.save()


def domain_change(request, domain_id):
    domain = Domains.objects.get(id=domain_id)
    manager = DomainManager()

    success, msg = manager.swap_domain(domain)

    return JsonResponse({
        'success': success,
        'message': msg,
        'domain_id': domain_id})


def test(request):
    return HttpResponse("testok")