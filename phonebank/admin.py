from django.contrib import admin
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
    list_filter = ['room', 'is_active']
    date_hierarchy = 'last_active'
    search_fields = ['uuid', 'email_address', 'nickname']


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    pass


@admin.register(TelnyxCredential)
class TelnyxCredentialAdmin(admin.ModelAdmin):
    list_display = ['id', 'agent']
    list_filter = ['agent']
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
    list_filter = ['statename', 'priority', 'provided_to']
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
