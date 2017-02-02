from datetime import timedelta

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from approver.constants import STATE_CHOICES, COUNTRY_CHOICES, QI_CHECK

from approver import utils
from approver import constants
from approver.models.bridge_models import Registerable
from approver.models.provenance import Provenance
from approver.models.tag_models import Tag, TagPrint, TaggedWithName
from approver.models.mesh_models import Descriptor


class DataList(Registerable):
    name = models.CharField(max_length=400)
    description = models.CharField(max_length=400, null=True)
    sort_order = models.IntegerField(null=True)
    tag_property_name = 'name'

    def __str__(self, delimiter=' '):
        return delimiter.join([self.name, self.description or ''])

    def get_natural_dict(self):
        return {
            'name': str(self.name),
            'description': str(self.description),
        }

    class Meta:
        abstract = True


class Organization(Provenance, Registerable):
    org_name = models.CharField(max_length= 400)

    def __str__(self, delimiter=' '):
        return self.org_name

class Training(Provenance, TagPrint, TaggedWithName, Registerable):
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=200, null=True)

class BigAim(Provenance, DataList):
    pass
class Category(Provenance, Tag):
    pass
class ClinicalArea(Provenance, Tag):
    pass
class ClinicalSetting(Provenance, Tag):
    pass
class Expertise(Provenance, Tag):
    pass
class Keyword(Provenance, Tag):
    pass
class Position(Provenance, Tag):
    pass
class QI_Interest(Provenance, Tag):
    pass
class Self_Classification(Provenance, DataList):
    pass

class Speciality(Provenance, Tag):
    name = models.CharField(max_length=80)

class Suffix(Provenance, Tag):
    pass

class FocusArea(Provenance, Tag):
    sort_order = models.IntegerField(null=True)
class ClinicalDepartment(Provenance, Tag):
    sort_order = models.IntegerField(null=True)

class Person(Provenance, Registerable):
    account_expiration_time = models.DateTimeField(null=True)
    business_phone = models.CharField(max_length=50, null=True)
    contact_phone = models.CharField(max_length=50, null=True)
    email_address = models.CharField(max_length=100, null=True)
    expertise = models.ManyToManyField(Expertise)
    first_name = models.CharField(max_length=30)
    gatorlink = models.CharField(max_length=50, null=True)
    last_login_time = models.DateTimeField(null=True)
    last_name = models.CharField(max_length=30)
    organization = models.ManyToManyField(Organization)
    position = models.ManyToManyField(Position)
    qi_interest = models.ManyToManyField(QI_Interest)
    speciality = models.ManyToManyField(Speciality)
    suffix = models.ManyToManyField(Suffix)
    training = models.CharField(max_length=50, null=True)
    user = models.OneToOneField(User, null=True, on_delete=models.CASCADE, related_name="person")
    webpage_url = models.CharField(max_length=50, null=True)
    title = models.CharField(max_length=50, null=True)
    department = models.CharField(max_length=50, null=True)
    qi_required = models.SmallIntegerField(null=True)
    clinical_area = models.ManyToManyField(ClinicalArea)
    self_classification = models.ForeignKey(Self_Classification, null=True, on_delete=models.SET_NULL,
                                            related_name="person")
    other_self_classification = models.CharField(max_length=100, null=True)
    tag_property_name = 'email_address'
    is_admin = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        try:
            for char in constants.invalid_email_characters:
                self.email_address = self.email_address.replace(char, '')
        except:
            pass
        try:
            contact = self.contact_set[0]
            contact.business_email = self.email_address
            contact.first_name = self.first_name
            contact.last_name = self.last_name
            contact.save(*args, **kwargs)
        except:
            pass
        super(Person, self).save(*args, **kwargs)

    def __str__(self):
        first = self.first_name or ''
        last = self.last_name or ''
        name = ', '.join([str(item) for item in [first, last] if len(item)])
        email = '(' + self.email_address + ')' if self.email_address else ''
        return ' '.join([name, email])

    def get_natural_dict(self):
        return {
            'gatorlink': self.gatorlink,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email_address': self.email_address,
            'model_class_name': self.__class__.__name__,
        }


class Project(Provenance, Registerable):
    advisor = models.ManyToManyField(Person, related_name="advised_projects")
    approval_date = models.DateTimeField(null=True)
    archived = models.BooleanField(default=False)
    big_aim = models.ForeignKey(BigAim, null=True, on_delete=models.SET_NULL, related_name="projects")
    category = models.ManyToManyField(Category, related_name='projects')
    clinical_area = models.ManyToManyField(ClinicalArea, related_name='projects')
    clinical_setting = models.ManyToManyField(ClinicalSetting)
    collaborator = models.ManyToManyField(Person, related_name="collaborations")
    description = models.TextField()
    measures = models.TextField()
    overall_goal = models.TextField()
    owner = models.ForeignKey(Person, null=True, on_delete=models.SET_NULL, related_name="projects")
    proposed_end_date = models.DateTimeField(null=True)
    proposed_start_date = models.DateTimeField(null=True)
    title = models.CharField(max_length=300)
    mesh_keyword = models.ManyToManyField(Descriptor, related_name='projects', null=True)
    sent_email_list = models.ManyToManyField(Person, related_name="emailed_for_projects")

    def __str__(self):
        title = self.title or 'NO TITLE'
        try:
            owner_gatorlink = str(self.owner.gatorlink)
        except:
            owner_gatorlink = 'NO GATORLINK FOR OWNER'
        return ' '.join([title, owner_gatorlink])

    def get_is_editable(self):
        """
        Returns true if the project is editable.
        Projects get locked down after they are approved
        or a year after their creation date.
        """
        if utils.check_is_date_past_year(self.created) or self.approval_date:
            return False
        return True

    def is_approved(self):
        return self.approval_date or self.in_registry

    def approve(self, user):
        self.approval_date = timezone.now()
        self.save(user)

    def get_natural_dict(self):
        return {
            'title': self.title,
            'description': self.description,
            'owner': self.owner.natural_key(),
            'collaborators': [item.natural_key() for item in self.collaborator.all()],
            'mesh_keyword': [item.natural_key() for item in self.mesh_keyword.all()],
            'model_class_name': self.__class__.__name__,
        }

    def get_need_advisor(self):
        """
        Determine if the project needs an advisor based on whether qi is a requirement for the owner.
        """
        return self.owner.qi_required == QI_CHECK['yes'] and len(self.advisor.all()) == 0

class Address(Provenance, Registerable):
    person = models.ForeignKey(Person, on_delete=models.CASCADE, null=True, blank=True, related_name="business_address")
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, related_name="org_address")
    address1 = models.CharField(max_length=50)
    address2 = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    zip_code = models.CharField(max_length=10, null=True, blank=True)
    state = models.CharField(max_length=2, choices=STATE_CHOICES, null=True, blank=True)
    country = models.CharField(max_length=2, choices=COUNTRY_CHOICES, null=True, blank=True)

    def __str__(self):
        return ' ; '.join([self.address1,
                           self.address2,
                           self.city,
                           self.zip_code,
                           self.state,
                           self.country])

    def get_natural_dict(self):
        return {
            'address1': self.address1,
            'address2': self.address2,
            'city': self.city,
            'zip_code': self.zip_code,
            'state': self.state,
            'country': self.country,
            'person': self.person.natural_key(),
        }
