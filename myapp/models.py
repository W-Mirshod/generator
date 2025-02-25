import os
import uuid
import random
import time
import logging
import requests

from django.db import models
from .generator import ImageRandomize
from .randomizer import Generator
from traceback import format_exc
from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)


class Domains(models.Model):
    id = models.AutoField(primary_key=True)
    domain = models.CharField(max_length=255, unique=True)
    ssl = models.BooleanField(default=False)
    valid = models.BooleanField(default=False)
    error = models.BooleanField(default=False)
    error_text = models.TextField(null=True)
    used = models.BooleanField(default=False)
    # for swapping old domains
    status = models.CharField(max_length=20, choices=[('available', 'Available'), ('in_use', 'In Use'), ('error', 'Error')], default='available')

    def get_sub(self):
        return Sub.objects.filter(domain=self)

    def take_ssl(self, subs=100):
        log = ''
        log_path = 'logs/'+str(uuid.uuid4())+".txt"
        self.error = False
        self.save()
        if subs > 50: subs = 50
        try:
            #assert False
            # проверить
            # создать сабы
            assert self.take_check()
            rand_sub = [Generator.random_name(True) for i in range(subs)]
            log += f'Sub:{rand_sub}\n'
            print(rand_sub)
            sub_cmd = "".join([' -d '+i+'.'+self.domain for i in rand_sub])

            cmd = f"certbot certonly --webroot -w /var/www/html --non-interactive --agree-tos --register-unsafely-without-email{sub_cmd} > {log_path}"
            log += f'Cmd:{cmd}\n'

            res = os.system(cmd)
            #res = os.system("whoami")
            #time.sleep(120)
            log += f'Result:{res}\n'
            assert res == 0
            self.error = False
            self.valid = True
            self.ssl = True
            self.error_text = str(log) + str(log_path)
            self.save()
            
            [Sub.objects.create(domain=self, name=i) for i in rand_sub]

            ssl_cert_path = f'/etc/letsencrypt/live/{rand_sub[0]}.{self.domain}/'

            # /etc/letsencrypt/live/artyard.wadineelum.com/privkey.pem
            # /etc/letsencrypt/live/artyard.wadineelum.com/fullchain.pem

            file = open('/etc/nginx/sites-enabled/default','r+')
            ...

            file.seek(0,2)
            file.write('\n\n')
            file.write('''server {
    listen 443 ssl;
    server_name '''+' '.join([i+'.'+self.domain for i in rand_sub])+''';

    
    ssl_certificate '''+ ssl_cert_path +'''fullchain.pem;
    ssl_certificate_key '''+ ssl_cert_path +'''privkey.pem;


    ssl_protocols TLSv1 TLSv1.1 TLSv1.2;
    ssl_prefer_server_ciphers on;
    ssl_ciphers 'ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES256-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:DHE-DSS-AES128-GCM-SHA256:kEDH+AESGCM:ECDHE-RSA-AES128-SHA256:ECDHE-ECDSA-AES128-SHA256:ECDHE-RSA-AES128-SHA:ECDHE-ECDSA-AES128-SHA:ECDHE-RSA-AES256-SHA384:ECDHE-ECDSA-AES256-SHA384:ECDHE-RSA-AES256-SHA:ECDHE-ECDSA-AES256-SHA:DHE-RSA-AES128-SHA256:DHE-RSA-AES128-SHA:DHE-DSS-AES128-SHA256:DHE-RSA-AES256-SHA256:DHE-DSS-AES256-SHA:DHE-RSA-AES256-SHA:AES128-GCM-SHA256:AES256-GCM-SHA384:AES128-SHA256:AES256-SHA256:AES128-SHA:AES256-SHA:AES:CAMELLIA:DES-CBC3-SHA:!aNULL:!eNULL:!EXPORT:!DES:!RC4:!MD5:!PSK:!aECDH:!EDH-DSS-DES-CBC3-SHA:!EDH-RSA-DES-CBC3-SHA:!KRB5-DES-CBC3-SHA';

    location / {
        include     /etc/nginx/uwsgi_params;
        uwsgi_pass uwsgi://localhost:8080;
    }
}''')

            file.close()
            return True

        except:
            self.error = True
            self.error_text = str(log) + str(log_path) + format_exc()
            self.save()
        return False
    
    def take_check(self):
        log = ''
        self.error = False
        self.valid = False
        self.save()
        try:
            assert 'testok' == requests.get(f'http://subdomaintest.{self.domain}/teeeeeeeeeeeest/', timeout=3).text
            self.valid = True
            self.save()
            return True
        except:
            self.error = True
            self.error_text = str(log) + format_exc()
            self.save()
        return False
    
    class Meta:
        verbose_name = 'Domain'
        verbose_name_plural = 'Domains'
    

class DomainsHold(models.Model):
    domain = models.ForeignKey(Domains, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Domain: {self.domain}"
    
    class Meta:
        verbose_name = 'Domain Hold'
        verbose_name_plural = 'Domains Hold'


class Sub(models.Model):
    domain = models.ForeignKey(Domains, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    
    def get_link(self, link):
        r = RandLink.objects.create(sub=self, origlink=link, link=Generator.random_name()+random.choice(['.php', '.html', '.htm', '.asp', '']))
        return f"{'https' if self.domain.ssl else 'http'}://{self.name}.{self.domain.domain}/{r.link}"

    def get_test(self):
        return f"""{'https' if self.domain.ssl else 'http'}://{self.name}.{self.domain.domain}"""

    class Meta:
        verbose_name = 'Sub'
        verbose_name_plural = 'Subs'


class Sessions(models.Model):
    id = models.AutoField(primary_key=True)
    createat = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=320, null=True)
    settings = models.TextField(null=True)
    domains = models.ManyToManyField(Domains,related_name="sessions_domains")
    links = models.ManyToManyField(Domains,related_name="sessions_links")

    def get_pictures(self):
        return Pictures.objects.filter(session=self)
    
    def get_zips(self):
        return Zips.objects.filter(session=self)

    def delete(self, *args, **kwargs):
        try: [i.delete() for i in Pictures.objects.filter(session=self)]
        except: pass
        try: [i.delete() for i in Zips.objects.filter(session=self)]
        except: pass

        super(Sessions, self).delete(*args, **kwargs)
    
    class Meta:
        verbose_name = 'Session'
        verbose_name_plural = 'Sessions'



class Pictures(models.Model):
    id = models.AutoField(primary_key=True)
    session = models.ForeignKey(Sessions, on_delete=models.CASCADE)
    createat = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=320, null=True)
    filename = models.CharField(max_length=320, null=True, default=uuid.uuid4)
    picture = models.BooleanField(default=True)

    text = models.CharField(max_length=2048, null=True)

    def delete(self, *args, **kwargs):
        try: os.remove(f'pics/{self.filename}')
        except: pass
        try: [i.delete() for i in RandPic.objects.filter(picture=self)]
        except: pass

        super(Pictures, self).delete(*args, **kwargs)


    def get_path(self):
        return f"/pics_reger/{self.filename}"

    def set_extension(self):
        magic_numbers = {
            'png': bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]),
            'jpg1': bytes([0xFF, 0xD8, 0xFF, 0xE0]),
            'jpg2': bytes([0xFF, 0xD8, 0xFF, 0xE1])
        }
        max_read_size = max(len(m) for m in magic_numbers.values()) 
        file = open(f'pics/{self.filename}', 'rb')
        file_head = file.read(max_read_size)
        file.close()
        if file_head.startswith(magic_numbers['png']):
            of = self.filename
            self.name += ".png"
            self.filename = str(of) + ".png"
            self.save()
            os.rename(f'pics/{of}', f'pics/{self.filename}')
        elif file_head.startswith(magic_numbers['jpg1']) or file_head.startswith(magic_numbers['jpg2']):
            of = self.filename
            self.name += ".jpg"
            self.filename = str(of) + ".jpg"
            self.save()
            os.rename(f'pics/{of}', f'pics/{self.filename}')
        else:
            of = self.filename
            self.name += ".unk"
            self.filename = str(of) + ".unk"
            self.save()
            os.rename(f'pics/{of}', f'pics/{self.filename}')

    def get_random_base64(self, amount):
        return ImageRandomize.randomize_base64(f'pics/{self.filename}', amount)

    def gen_random_link(self, sub, amount):
        rndpic = RandPic.objects.create(picture=self, sub=sub, name=Generator.random_name()+".png")
        #ImageRandomize.randomize(f'pics/{self.filename}', amount, f'rand_pics/{rndpic.filename}.png')
        return f"""{'https://' if sub.domain.ssl else 'http://'}{sub.name}.{sub.domain.domain}/{rndpic.name}"""

    class Meta:
        verbose_name = 'Picture'
        verbose_name_plural = 'Pictures'


class RandPic(models.Model):
    id = models.AutoField(primary_key=True)
    picture = models.ForeignKey(Pictures, on_delete=models.CASCADE, blank=True, null=True)
    sub = models.ForeignKey(Sub, on_delete=models.CASCADE)
    createat = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=255, unique=True)
    filename = models.CharField(max_length=320, null=True, default=uuid.uuid4)

    rb = models.BooleanField(default=False)
    w = models.IntegerField(default=0)
    h = models.IntegerField(default=0)
    amount = models.IntegerField(default=0)

    def delete(self, *args, **kwargs):
        try: os.remove(f'rand_pics/{self.filename}.png')
        except: pass

        super(RandPic, self).delete(*args, **kwargs)

    def check_file(self):
        if self.rb:
            try: 
                assert os.path.exists(f'rand_pics/{self.filename}.png','rb').read()
                print('rp ok')
            except:
                print("gen file")
                ImageRandomize.random_blank(f'rand_pics/{self.filename}.png', self.w, self.h, True, self.amount)

        else:
            try: 
                assert os.path.exists(f'rand_pics/{self.filename}.png','rb').read()
                print('rp ok')
            except:
                print("gen file")
                ImageRandomize.randomize(f'pics/{self.picture.filename}', 16, f'rand_pics/{self.filename}.png')
   
    class Meta:
        verbose_name = 'RandPic'
        verbose_name_plural = 'RandPics'


class RandLink(models.Model):
    id = models.AutoField(primary_key=True)
    sub = models.ForeignKey(Sub, on_delete=models.CASCADE)
    createat = models.DateTimeField(auto_now_add=True)
    link = models.CharField(max_length=255, unique=True)
    origlink = models.CharField(max_length=1024, null=True)

    class Meta:
        verbose_name = 'RandLink'
        verbose_name_plural = 'RandLinks'


class Zips(models.Model):
    session = models.ForeignKey(Sessions, on_delete=models.CASCADE)
    filename = models.CharField(max_length=320, null=True, default=uuid.uuid4)
    done = models.BooleanField(default=False)
    error = models.BooleanField(default=False)
    error_text = models.TextField(null=True)

    def delete(self, *args, **kwargs):
        try: os.remove(f'pics/{self.filename}.zip')
        except: pass

        super(Zips, self).delete(*args, **kwargs)

    def get_path(self):
        return f"/pics_reger/{self.filename}.zip"

    def get_size(self):
        try:
            size = os.path.getsize(f'pics/{self.filename}.zip')
            if size < 1024:
                return f"{size} bytes"
            elif size < pow(1024,2):
                return f"{round(size/1024, 2)} KB"
            elif size < pow(1024,3):
                return f"{round(size/(pow(1024,2)), 2)} MB"
            elif size < pow(1024,4):
                return f"{round(size/(pow(1024,3)), 2)} GB"
        except:
            return '-'
        
    class Meta:
        verbose_name = 'Zip'
        verbose_name_plural = 'Zips'


class DomainManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)


    def check_domain_status(self, domain):
        try:
            response = requests.get(
                f'http://subdomaintest.{domain.domain}/teeeeeeeeeeeest/',
                timeout=(3, 10)  # connect & read
            )
            if response.status_code == 200 and response.text == 'testok':
                return True
            return False
        except requests.RequestException as e:
            self.logger.error(f"Error checking domain {domain.domain}: {e}")
            return False
    def find_replacement_domain(self):
        """
        Finds an available domain from the hold pool.
        Returns the replacement domain or None if none available.
        """
        available_domains = DomainsHold.objects.filter(
            domain__status='available'
        ).order_by('added_at').first()
        
        if available_domains:
            return available_domains.domain
        return None
    
    class Meta:
        verbose_name = 'Domain'
        verbose_name_plural = 'Domains'
    

    @transaction.atomic
    def swap_domain(self, old_domain):
        try:
            replacement = self.find_replacement_domain()
            if not replacement:
                msg = f"No replacement domain available for {old_domain.domain}"
                self.logger.warning(msg)
                return False, msg

            old_domain.status = 'error'
            old_domain.valid = False
            old_domain.error = True
            old_domain.error_text = f"Domain down and swapped at {timezone.now()}"
            old_domain.save()


            replacement.status = 'in_use'
            replacement.valid = True
            replacement.error = False
            replacement.used = False
            replacement.save()

            if old_domain.ssl and not replacement.ssl:
                ssl_success = replacement.take_ssl(50)  # 50 subdomains
                if not ssl_success:
                    return False, f"Failed to setup SSL for replacement domain {replacement.domain}"

            self.update_domain_references(old_domain, replacement)

            msg = f"Successfully swapped {old_domain.domain} with {replacement.domain}"
            self.logger.info(msg)
            return True, msg

        except Exception as e:
            msg = f"Error during domain swap: {str(e)}"
            self.logger.exception(msg)
            return False, msg


    def update_domain_references(self, old_domain, new_domain):
        old_domain.sessions_domains.all().update(domains=new_domain)
        old_domain.sessions_links.all().update(links=new_domain)
        
        Sub.objects.filter(domain=old_domain).update(domain=new_domain)


    def check_and_swap_domains(self):
        results = []
        active_domains = Domains.objects.filter(status='in_use', error=False)
        
        for domain in active_domains:
            if not self.check_domain_status(domain):
                success, msg = self.swap_domain(domain)
                results.append((domain, success, msg))
                
        return results

    def add_domain_to_hold(self, domain):
        try:
            with transaction.atomic():
                domain.status = 'available'
                domain.save()
                DomainsHold.objects.create(domain=domain)
                return True
        except Exception as e:
            self.logger.error(f"Error adding domain to hold: {e}")
            return False
        
    class Meta:
        verbose_name = 'Domain'
        verbose_name_plural = 'Domains'


def schedule_domain_checks():
    from django.core.cache import cache
    import threading
    import time
    
    def check_domains_periodically():
        manager = DomainManager()
        while True:
            try:
                results = manager.check_and_swap_domains()
                for domain, success, msg in results:
                    if not success:
                        logger.error(f"Failed to swap domain {domain.domain}: {msg}")
            except Exception as e:
                logger.exception("Error in domain check loop")
            time.sleep(300)  # 300 seconds, if we can manually change according to our needs
            
    if not cache.get('domain_check_running'):
        cache.set('domain_check_running', True)
        thread = threading.Thread(target=check_domains_periodically, daemon=True)
        thread.start()

    class Meta:
        verbose_name = 'Domain'
        verbose_name_plural = 'Domains'


class TelegramAPI(models.Model):
    telegram_listed = models.BooleanField(default=False)
    telegram_enabled = models.BooleanField(default=False)
    telegram_error = models.TextField(null=True, blank=True)
    telegram_last_checked = models.DateTimeField(null=True)

    class Meta:
        verbose_name = 'Telegram API'
        verbose_name_plural = 'Telegram API'


class RedirectCounter(models.Model):
    link = models.ForeignKey(RandLink, on_delete=models.CASCADE)
    count = models.IntegerField(default=0)
    last_redirect = models.DateTimeField(auto_now=True)

    def increment(self):
        self.count += 1
        self.save()

    class Meta:
        verbose_name = 'Redirect Counter'
        verbose_name_plural = 'Redirect Counters'
