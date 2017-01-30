from approver.models import Person, Project, Keyword, ClinicalArea, ClinicalSetting, BigAim, Descriptor, Contact
from approver.constants import SESSION_VARS
from approver.utils import extract_tags, update_tags, extract_model
import approver.utils as utils

from django.contrib.auth.models import User
from django.utils import timezone, dateparse
from django.db.models.query import QuerySet
from django.db.models import Q
from approver.constants import description_factor,keyword_factor,title_factor,big_aim_factor,category_factor,clinical_area_factor,clinical_setting_factor


def create_or_update_project(current_user, project_form, project_id=None):
    """
    Creates a new project or updates and existing one using a project form
    """
    project = None
    if project_exists(project_id):
        project = Project.objects.get(id=project_id)
        update_project_from_project_form(project, project_form, current_user)
    else:
        project = create_new_project_from_user_form(current_user, project_form)
    return project

def create_new_project_from_user_form(current_user, form):
    """
    This function creates a project using user information
    from the current session and a title
    """
    now = timezone.now()
    person = current_user.person

    new_project = Project(owner=person, title=form.get('title'))

    new_project.save(last_modified_by=current_user)

    update_project_from_project_form(new_project, form, current_user)

    return new_project

def __is_email(tag):
    if '@' in tag:
        return tag

def __is_valid(tag):
    if __is_email(tag):
        return tag
    elif len(tag) == 32:
        return tag

def __clean_tag(tag):
    return tag.replace('NEW::', '').replace(';', '')

def __new_person_from_contact(contact, user):
    person = contact.new_person()
    person.save(user)
    contact.person = person
    contact.save(user)
    return person

def get_person(tag, user):
    # see if tag is guid or not
    cleaned = __clean_tag(tag)

    if __is_email(cleaned):
        contact = Contact(business_email=cleaned)
        # contact.save(user)
        return __new_person_from_contact(contact, user)
    else:
        contact = Contact.objects.get(guid=tag).select_related('person')
        try:
            person = contact.person
        except:
            person = None
        if person:
            return person
        else:
            return __new_person_from_contact(contact, user)


def update_project_from_project_form(project, project_form, editing_user):
    """
    This function changes an existing project entry
    based on the information in the project_form.
    This will not work if the project does not yet
    exist.
    """
    now = timezone.now()
    parse_date = dateparse.parse_date

    project.title = project_form.get('title')
    project.description = project_form.get('description')
    project.overall_goal = project_form.get('overall_goal')
    project.measures = project_form.get('measures')
    project.proposed_start_date = parse_date(project_form.get('proposed_start_date'))
    project.proposed_end_date = parse_date(project_form.get('proposed_end_date'))
    project.big_aim = extract_model(BigAim, "name", project_form.get('select-big_aim'))

    advisor = [get_person(tag, editing_user) for tag in extract_tags(project_form, 'advisor') if __is_valid(tag)]
    collaborator = [get_person(tag, editing_user) for tag in extract_tags(project_form, 'collaborator') if __is_valid(tag)]
    clinical_area = extract_tags(project_form, 'clinical_area')
    clinical_setting = extract_tags(project_form, 'clinical_setting')
    mesh_keyword = extract_tags(project_form, 'mesh_keyword')

    update_tags(model=project,
                tag_property='mesh_keyword',
                tags=mesh_keyword,
                tag_model=Descriptor,
                tagging_user=editing_user)

    update_tags(model=project,
                tag_property='clinical_area',
                tags=clinical_area,
                tag_model=ClinicalArea,
                tagging_user=editing_user)

    update_tags(model=project,
                tag_property='clinical_setting',
                tags=clinical_setting,
                tag_model=ClinicalSetting,
                tagging_user=editing_user)

    project.collaborator = collaborator
    project.advisor = advisor

    project.save(editing_user)

def get_project_or_none(project_id):
    """
    This returns a project instance if it exists or it returns None
    """
    try:
        project = Project.objects.get(id=project_id)
        return project
    except:
        return None

def project_exists(project_id):
    """
    This returns a boolean for if the project exists or not
    """
    return (len(Project.objects.filter(id=project_id)) > 0)

def current_user_is_superuser(current_user):
    return current_user.person.is_admin

def current_user_is_project_owner(current_user, project):
    """
    This returns a boolean about if the current_user.person.id is the
    same as the project.owner.id
    """
    return current_user.person.id == project.owner.id

def is_current_project_editable(current_user,project):
    return current_user_is_superuser(current_user) or (
           current_user_is_project_owner(current_user, project) and
           project.get_is_editable())

def current_user_is_project_advisor_or_collaborator(current_user, project):
    """
    This returns a boolean true if the current_user.person.id is in 
    project.advisor or project.collaborator
    """
    for advisor in project.advisor.all():
        if current_user.person.id == advisor.id:
            return True
    for collaborator in project.collaborator.all():
        if current_user.person.id == collaborator.id:
            return True
    return False
def current_user_can_perform_project_delete(current_user,project):
    """
    This returns an error message if user cannot delete the project, returns empty String when
    user is the owner for the project and the project is editable.
    """
    toast_message = ""
    if current_user.person.is_admin:
        project.delete(current_user)
        return 'Deleted Project'
    if(toast_message == "" and project is None):
        toast_message = 'Project with id {} does not exist.'.format(project_id)
        return toast_message
    if(toast_message == "" and current_user_is_project_owner(current_user, project) is not True):
        return 'You are not authorized to delete this project.'
    if (toast_message == "" and project.get_is_editable() is not True):
        return 'You are not allowed to delete/edit this project.'
    project.delete(current_user)
    return 'Deleted Project'

def current_user_can_archive_project(current_user,project):
    """Only Super User can archive projects"""
    project.archived = True
    project.save(current_user)
    return 'Archived Project'

def current_user_can_unarchive_project(current_user,project):
    """Only Super User can unarchive projects"""
    project.archived = False
    project.save(current_user)
    return 'UnArchived Project'

def get_approved_projects():
    """
    This returns a list of all the existing approved projects
    """
    return Project.objects.exclude(approval_date__isnull=True)

def get_similar_projects(project):
    projects = get_approved_projects()
    project_scores = []

    for member in projects:
        similarity = _calculate_similarity_score(project, member)
        if similarity != 0:
            project_scores.append((member.id, member, similarity))

    return sorted(project_scores, key=lambda score: score[2], reverse = True)

def _calculate_similarity_score(project, member):

    '''
    Need to be improved based on priority.
    Sum can be 100 to scale from zero to 100 (like a percentage)
    '''

    similarity = 0.0

    if project.title is not None and member.title is not None:
        similarity += title_factor * _jaccard_similarity(project.title, member.title)

    if project.mesh_keyword is not None and member.mesh_keyword is not None:
        similarity += keyword_factor * _jaccard_similarity(project.mesh_keyword.all(), member.mesh_keyword.all())

    if project.description is not None and member.description is not None:
        similarity += description_factor * _jaccard_similarity(project.description, member.description)

    if project.big_aim is not None and member.big_aim is not None:
        similarity += big_aim_factor * _jaccard_similarity(project.big_aim.name, member.big_aim.name)

    if project.clinical_setting is not None and member.clinical_setting is not None:
        similarity += clinical_setting_factor * _jaccard_similarity(project.clinical_setting.all(), member.clinical_setting.all())

    if project.clinical_area is not None and member.clinical_area is not None:
        similarity += clinical_area_factor * _jaccard_similarity(project.clinical_area.all(), member.clinical_area.all())

    if project.category is not None and member.category is not None:
        similarity += category_factor * _jaccard_similarity(project.category.all(), member.category.all())

    return similarity


def _get_set_for_query(queryset):
    res = set()
    for element in queryset.all():
        res.add(getattr(element, element.tag_property_name))
    return res

def _jaccard_similarity(doc1, doc2):

    a = set()
    b = set()

    if isinstance(doc1, QuerySet):
        a = _get_set_for_query(doc1)
        b = _get_set_for_query(doc2)
    else:
        a = set(doc1.split())
        b = set(doc2.split())

    intersection = len(a.intersection(b))

    if intersection == 0: return intersection

    similarity = float(intersection*1.0/len(a.union(b)))
    return similarity
