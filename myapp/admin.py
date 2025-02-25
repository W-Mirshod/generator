from django.contrib import admin
from django.contrib.auth.models import Group
import myapp.models as models


admin.site.unregister(Group)

@admin.register(models.Domains)
class DomainsAdmin(admin.ModelAdmin):
    list_display = ('domain', 'ssl', 'valid', 'error', 'status')
    list_filter = ('ssl', 'valid', 'error', 'status')
    search_fields = ('domain',)
    actions = ['mark_valid', 'mark_invalid']

    def mark_valid(self, request, queryset):
        queryset.update(valid=True, error=False)
    mark_valid.short_description = "Mark selected domains as valid"

    def mark_invalid(self, request, queryset):
        queryset.update(valid=False, error=True)
    mark_invalid.short_description = "Mark selected domains as invalid"

@admin.register(models.DomainsHold)
class DomainsHoldAdmin(admin.ModelAdmin):
    list_display = ('domain', 'added_at')
    list_filter = ('added_at',)

@admin.register(models.Sub)
class SubAdmin(admin.ModelAdmin):
    list_display = ('name', 'domain')
    list_filter = ('domain',)
    search_fields = ('name', 'domain__domain')

@admin.register(models.Sessions)
class SessionsAdmin(admin.ModelAdmin):
    list_display = ('id', 'createat', 'name')
    list_filter = ('createat',)
    search_fields = ('name',)
    filter_horizontal = ('domains', 'links')

@admin.register(models.Pictures)
class PicturesAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'createat', 'name', 'filename')
    list_filter = ('createat', 'session')
    search_fields = ('name', 'filename')

@admin.register(models.RandPic)
class RandPicAdmin(admin.ModelAdmin):
    list_display = ('id', 'picture', 'sub', 'createat', 'name')
    list_filter = ('createat', 'sub')
    search_fields = ('name',)

@admin.register(models.RandLink)
class RandLinkAdmin(admin.ModelAdmin):
    list_display = ('id', 'sub', 'createat', 'link', 'origlink')
    list_filter = ('createat', 'sub')
    search_fields = ('link', 'origlink')

@admin.register(models.Zips)
class ZipsAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'filename', 'done', 'error')
    list_filter = ('done', 'error', 'session')
    search_fields = ('filename',)

@admin.register(models.TelegramAPI)
class TelegramAPIAdmin(admin.ModelAdmin):
    list_display = ('telegram_listed', 'telegram_enabled', 'telegram_error', 'telegram_last_checked')
    list_filter = ('telegram_listed', 'telegram_enabled')

@admin.register(models.RedirectCounter)
class RedirectCounterAdmin(admin.ModelAdmin):
    list_display = ('link', 'count', 'last_redirect')
    list_filter = ('last_redirect',)
    search_fields = ('link__link',)
