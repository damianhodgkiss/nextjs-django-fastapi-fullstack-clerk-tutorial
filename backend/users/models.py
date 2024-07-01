from django.db import models
from django_use_email_as_username.models import BaseUser, BaseUserManager
from .schemas import ClerkWebhook, ClerkWebhookEvent


class User(BaseUser):
    objects = BaseUserManager()

    clerk_id = models.CharField(max_length=255, blank=True, null=True)

    @classmethod
    def handle_clerk_webhook(cls, event: ClerkWebhook):
        if event.type in [
            ClerkWebhookEvent.user_created,
            ClerkWebhookEvent.user_updated,
        ]:
            data = event.data
            clerk_id: str = data.get("id")
            # lookup user by clerk_id
            try:
                user: User = cls.objects.get(clerk_id=clerk_id)
            except cls.DoesNotExist:
                primary_email: str | None = next(
                    (
                        email.get("email_address")
                        for email in data.get("email_addresses", [])
                        if email.get("id") == data.get("primary_email_address_id")
                    ),
                    None,
                )
                try:
                    # lookup user by email address
                    user: User = cls.objects.get(email=primary_email)
                    user.clerk_id = clerk_id
                except cls.DoesNotExist:
                    user: User = cls(clerk_id=clerk_id)
                    user.email = primary_email

            user.first_name = data.get("first_name")
            user.last_name = data.get("last_name")

            user.save()
        elif event.type == ClerkWebhookEvent.user_deleted:
            data = event.data
            clerk_id: str = data.get("id")
            try:
                user: User = cls.objects.get(clerk_id=clerk_id)
                user.delete()
            except cls.DoesNotExist:
                pass


class OrganizationMembership(models.Model):
    ROLE_CHOICES = [
        ("org:member", "Member"),
        ("org:admin", "Admin"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    organization = models.ForeignKey("Organization", on_delete=models.CASCADE)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default="org:member")

    def __str__(self) -> str:
        return f"{self.user} -  {self.role} in {self.organization}"

    class Meta:
        unique_together = ("user", "organization")


class Organization(models.Model):
    name = models.CharField(max_length=255)
    users = models.ManyToManyField(
        User, through=OrganizationMembership, related_name="organizations"
    )
    clerk_id = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name

    @classmethod
    def handle_clerk_webhook(cls, event: ClerkWebhook):
        data = event.data
        if event.type in [
            ClerkWebhookEvent.organization_created,
            ClerkWebhookEvent.organization_updated,
        ]:
            clerk_id: str = data.get("id")
            try:
                organization: Organization = cls.objects.get(clerk_id=clerk_id)
            except cls.DoesNotExist:
                organization: Organization = cls(clerk_id=clerk_id)

            organization.name = data.get("name")
            organization.save()
        elif event.type == ClerkWebhookEvent.organization_deleted:
            clerk_id: str = data.get("id")
            try:
                organization: Organization = cls.objects.get(clerk_id=clerk_id)
                organization.delete()
            except cls.DoesNotExist:
                pass
        elif event.type in [
            ClerkWebhookEvent.organization_membership_created,
            ClerkWebhookEvent.organization_membership_updated,
        ]:
            org = data.get("organization")
            public_user_data = data.get("public_user_data")

            organization_clerk_id: str = org.get("id")
            user_clerk_id: str = public_user_data.get("user_id")
            role: str = data.get("role", "org:member")

            try:
                organization: Organization = cls.objects.get(clerk_id=organization_clerk_id)
                # add user to organization
                user: User = User.objects.get(clerk_id=user_clerk_id)
                OrganizationMembership.objects.update_or_create(
                    user=user, organization=organization, defaults={"role": role}
                )
            except cls.DoesNotExist:
                pass
            except User.DoesNotExist:
                pass
        elif event.type == ClerkWebhookEvent.organization_membership_deleted:
            org = data.get("organization")
            public_user_data = data.get("public_user_data")

            organization_clerk_id: str = org.get("id")
            user_clerk_id: str = public_user_data.get("user_id")

            try:
                organization: Organization = cls.objects.get(clerk_id=organization_clerk_id)
                user: User = User.objects.get(clerk_id=user_clerk_id)
                OrganizationMembership.objects.filter(
                    user=user, organization=organization
                ).delete()
            except cls.DoesNotExist:
                pass
            except User.DoesNotExist:
                pass


class OrganizationWithRole(Organization):
    class Meta:
        proxy = True

    def __init__(self, *args, **kwargs):
        self._role: str | None = kwargs.pop("role", None)
        super().__init__(*args, **kwargs)

    @property
    def role(self) -> str | None:
        return self._role

    @classmethod
    def from_org_and_role(cls, organization: Organization, role: str):
        instance: OrganizationWithRole = cls(
            **{
                field.name: getattr(organization, field.name)
                for field in organization._meta.fields
            }
        )
        instance._role = role
        return instance
