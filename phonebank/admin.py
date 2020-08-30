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


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    pass


@admin.register(TelnyxCredential)
class TelnyxCredentialAdmin(admin.ModelAdmin):
    pass


class VoterResource(resources.ModelResource):

    class Meta:
        model = Voter


@admin.register(Voter)
class VoterAdmin(ImportExportActionModelAdmin):
    resource_class = VoterResource


# Customize admin site appearance.
admin.AdminSite.site_header = "Boran"
admin.AdminSite.site_title = "Phonebank"
admin.AdminSite.index_title = "Data management"
