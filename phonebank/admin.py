from urllib.parse import urlparse

from django.conf import settings
from django.contrib import admin, messages
from django.utils.translation import ngettext
from import_export import resources
from import_export.admin import ImportExportActionModelAdmin

from phonebank.models import Agent, TelnyxCredential, Room, Voter


class AgentResource(resources.ModelResource):

    class Meta:
        model = Agent
        import_id_fields = ('uuid',)


@admin.register(Agent)
class AgentAdmin(ImportExportActionModelAdmin):
    resource_class = AgentResource
    list_display = [
        'nickname', 'email_address', 'room', 'is_active', 'last_active',
        'provided_count',
    ]
    list_filter = [('room', admin.RelatedOnlyFieldListFilter), 'is_active']
    date_hierarchy = 'last_active'
    search_fields = ['uuid', 'email_address', 'nickname']
    actions = ['enable_access', 'disable_access', 'show_access_links']

    @admin.action(permissions=['change'])
    def enable_access(self, request, queryset):
        updated = queryset.filter(is_active=False).update(is_active=True)
        self.message_user(
            request,
            ngettext(
                "{} agent was enabled.",
                "{} agents were enabled.",
                updated,
            ).format(updated),
            messages.SUCCESS,
        )

    @admin.action(permissions=['change'])
    def disable_access(self, request, queryset):
        updated = queryset.filter(is_active=True).update(is_active=False)
        for telnyx_credential in TelnyxCredential.objects.exclude(
            agent__is_active=True,
        ):
            telnyx_credential.delete()
        self.message_user(
            request,
            ngettext(
                "{} agent was disabled.",
                "{} agents were disabled.",
                updated,
            ).format(updated),
            messages.SUCCESS,
        )

    @admin.action(permissions=['view'])
    def show_access_links(self, request, queryset):
        for agent in queryset:
            url = request.build_absolute_uri(agent.get_absolute_url())
            if not settings.DEBUG:
                # Alternatively, set Django setting SECURE_PROXY_SSL_HEADER.
                url = urlparse(url)._replace(scheme='https').geturl()
            self.message_user(
                request,
                "Access link for {}: {}".format(
                    agent.nickname,
                    url,
                ),
            )


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    pass


@admin.register(TelnyxCredential)
class TelnyxCredentialAdmin(admin.ModelAdmin):
    list_display = ['id', 'agent']
    list_filter = [('agent', admin.RelatedOnlyFieldListFilter)]
    search_fields = ['id', 'agent__nickname']

    def delete_queryset(self, request, queryset):
        # Delete selected objects individually instead of in bulk
        # in order to call the model's delete method, which deletes
        # the credential through the Telnyx API.
        for telnyx_credential in queryset:
            telnyx_credential.delete()


class VoterResource(resources.ModelResource):

    class Meta:
        model = Voter


@admin.register(Voter)
class VoterAdmin(ImportExportActionModelAdmin):
    resource_class = VoterResource
    list_display = [
        'id', 'statename', 'name_last', 'name_first', 'name_middle',
        'priority', 'provided_to', 'provided_at',
    ]
    list_filter = [
        'priority',
        ('provided_to', admin.RelatedOnlyFieldListFilter),
        ('statename', admin.AllValuesFieldListFilter),
    ]
    date_hierarchy = 'provided_at'
    search_fields = [
        'id', 'name_last', 'name_first', 'name_middle',
        'cell_phone_1', 'cell_phone_2', 'land_phone_1', 'land_phone_2',
        'notes',
    ]


# Customize admin site appearance.
admin.AdminSite.site_header = "Boran"
admin.AdminSite.site_title = "Phonebank"
admin.AdminSite.index_title = "Data management"
