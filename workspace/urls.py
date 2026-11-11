from django.urls import path

from workspace import views

app_name = "workspace"

urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("members/", views.MembersView.as_view(), name="members"),
    path("members/invite/", views.InviteMemberView.as_view(), name="invite-member"),
    path("members/<int:user_id>/role/", views.UpdateMemberRoleView.as_view(), name="member-role"),
    path("members/<int:user_id>/remove/", views.RemoveMemberView.as_view(), name="member-remove"),
    path(
        "members/ownership/transfer/",
        views.TransferOwnershipView.as_view(),
        name="ownership-transfer",
    ),
    path(
        "invitations/accept/<uuid:token>/",
        views.AcceptInvitationView.as_view(),
        name="accept-invitation",
    ),
    path("projects/", views.ProjectsView.as_view(), name="projects"),
    path("settings/profile/", views.ProfileView.as_view(), name="profile"),
    path("settings/audit-log/", views.AuditLogView.as_view(), name="audit-log"),
]
