from datetime import timedelta
import uuid

import django
from django.contrib.auth.models import User
from django.core.exceptions import MultipleObjectsReturned
from django.core.urlresolvers import reverse
from django.shortcuts import redirect, render
from django.utils import timezone

from datetime import timedelta

import approver.constants as constants
import django
from django.db.models import fields
from django.apps import apps

def shib_enabled():
    return constants.SHIB_ENABLED == 'true'

def is_callable(item):
    """
    Used to check if items in a module are functions
    """
    try:
        getattr(item, '__call__')
        return True
    except:
        return False

def user_exists(about_you_form):
    """
    Returns True if user exists, and False otherwise given an
    about_you_form
    """
    return (len(User.objects.filter(username=about_you_form.get('user_name'))) != 0)

def layout_render(request, context):
    """
    This function should be used in place of render.
    It adds context['content'] into the layout.html so that the nav bar is
    present as well as css and javascript
    """
    context['base_url'] = constants.base_url
    context['registry_search_url'] = constants.registry_search_path
    context['faq_url'] = constants.registry_hostportpath
    context['staging_bar_display'] = '' if constants.is_staging else 'none'
    return render(request, 'approver/layout.html', context)

def get_current_user_gatorlink(request):
    """
    Gets the current user's gatorlink
    We don't return the user here because the util file shall
    not have a dependency on the models
    """
    if shib_enabled():
        return request.META.get('HTTP_GLID')
    else:
        return request.session.get(constants.SESSION_VARS['gatorlink'])

def get_and_reset_toast(session):
    toast = session.get("toast_text")
    session['toast_text'] = ''
    return toast

def set_toast(session, toast_text):
    session['toast_text'] = toast_text

def project_redirect_and_toast(request, project_id, toast_text):
    request.session['toast_text'] = toast_text
    return redirect(reverse("approver:projects", kwargs={'project_id':project_id}))

def about_you_redirect_and_toast(request, toast_text):
    request.session['toast_text'] = toast_text
    return redirect(reverse("approver:aboutyou"))

def dashboard_redirect_and_toast(request, toast_text):
    request.session['toast_text'] = toast_text
    return redirect(reverse("approver:dashboard"))

def dashboard_su_redirect_and_toast(request, toast_text):
    request.session['toast_text'] = toast_text
    return redirect(reverse("approver:dashboard_su"))

def userlist_su_redirect_and_toast(request, toast_text):
    request.session['toast_text'] = toast_text
    return redirect(reverse("approver:userlist"))

def after_approval(project):
    return redirect(reverse("approver:project_status") + str(project.id))

def set_guid_if_empty(model):
    if not model.guid:
        model.guid = get_guid()

def get_guid():
    return uuid.uuid4().hex

def set_created_by_if_empty(model, user):
    """
    This function is called by our save function because django
    throws exceptions on object access if something doesn't exist.
    You cannot dereference a related field if it doesn't exist.
    Meaning you have to do a try except block.
    """
    try:
        # the following line throws an exception
        model.created_by is not None
    except:
        model.created_by = user

def get_id_or_none(model):
    """
    Django explodes if you dereference pk before saving to the db
    """
    try:
        return model.id
    except:
        return None

def format_date(date):
    """
    This format date is used with the date picker. It has to be in a
    particular form in order to work
    """
    date_parts = [date.year, date.month, date.day]
    return '/'.join([str(part) for part in date_parts])

def is_guid(tag):
    try:
        hex = int(tag.upper(), 16)
        return len(tag) == 32
    except:
        return False

def clean_tag(tag):
    return tag.replace('NEW::', '').replace(';', '')

def extract_tags(form, tag_field_name):
    """
    This function extracts the tags from a form and returns
    a list of their names.
    """
    invisible_space = u"\u200B"
    split_character = ';'
    tags = form.get(tag_field_name)
    tags = tags.split(';')
    for tag in tags:
        if tag == '':
            tags.remove('')
    return [tag.replace(invisible_space, '') for tag in tags]

def model_matching_tag(tag_text, model_class, current_user, matching_property='guid'):
    """
    This returns the model where
    model_class.objects.filter(model_class.tag_property_name=tag_text)
    or
    model_class.objects.filter(matching_property=tag_text)
    if no model matches, make a new one with the current_user
    if more than one model exists, return None
    """
    cleaned = clean_tag(tag_text)

    if is_guid(cleaned):
        models = model_class.objects.filter(guid=cleaned)
        if len(models) is 1:
            return models[0]
        else:
            return None
    else:
        model = model_class()
        setattr(model, model.tagged_with, cleaned)
        model.save(current_user)
        return model


def update_tags(model, tag_property, tags, tag_model, tagging_user):
    """
    Given a model to update,
    a model.tag_property to change,
    a list of strings called tags to add,
    a tag_model to which those tags belong,
    and a tagging_user who is doing the tagging
    This function will add those tags to the model by
    the tagging user and create new tag_models if the
    particular tag does not exist

    if any tag matches against more than one model as determined
    by tag_model.tag_property_name, those models will NOT be added
    """
    taggable = getattr(model, tag_property)
    taggable.clear()

    tag_models = [model_matching_tag(tag, tag_model, tagging_user) for tag in tags]

    for tag in tag_models:
        if isinstance(tag, tag_model):
            taggable.add(tag)

    # this should do a diff and only save if it changed
    # either that or save all the diffrent tag types at once
    return model

def get_related(model, related_model_name):
    """
    Given a model,
    a related_model_name

    this function returns a list of
    model.related_model
    or an empty list
    Example: get_related(Person, 'project')  will return all projects related to a person
    """
    model_in_db = getattr(model, 'pk')
    if model_in_db:
        return getattr(model, related_model_name).all()
    else:
        return []

def get_related_property(model, related_model_name, related_model_property='name'):
    """
    Given a model,
    a related_model_name,
    and a related_model_property

    this function returns a list of
    model.related_model.related_model_property
    or an empty list
    Example: get_related_property(Person, 'project', 'title')  will return all project titles related to a person
    """
    relateds = get_related(model, related_model_name)
    list_of_related_properties = [getattr(item, related_model_property) for item in relateds]
    return [prop for prop in list_of_related_properties if prop != None]

def check_fields(ModelName,fieldname,type,max_length=None):
    """
    Given a Model checks if the fieldname is of proper type.
    Also checks the max_length if it is not None
    """
    model_meta = getattr(ModelName, "_meta")
    fields = getattr(model_meta, "fields")
    for field in fields :
        if field.name == fieldname:
            if isinstance(field, getattr(django.db.models.fields, type+"Field")) == True :
                if max_length is not None :
                    if field.max_length == max_length :
                        return True
                else:
                    return True
            else:
                return False

def get_account_expiration_date(date):
    """Account expiration date is an year from last login date"""
    return date + timedelta(days=365)

def check_is_date_past_year(date):
    return date + timedelta(days=365) < timezone.now()

def get_or_instantiate(Model, kwargs):
    """
    This tries to get a model matching the kwargs.
    If it cant be found. It will instantiate one.
    NOTE: this will not save the object
    """
    try:
        return Model.objects.get(**kwargs)
    except:
        return Model(**kwargs)

def save_all(iterable, user):
    """
    Saves every item in iterable with the user passed
    NOTE: This will exhaust iterators, Take care
    """
    for item in iterable:
        item.save(user)


def is_not_none(item):
    return item != None

def true_false_to_bool(true_false_string):
    """
    This function will take a string with a value of
    true or false and return a boolean object representation
    of it
    """
    if true_false_string is not None:
        if (true_false_string.lower() == 'true'):
            return True
        elif (true_false_string.lower() == 'false'):
            return False

    return None

def get_model_from_string(model_name):
    """
    This function will take a string name and try to find
    a model match of it.
    """
    app_models = apps.get_app_config(constants.app_label).get_models()
    for model in app_models:
        if(model.__name__.lower() == model_name.lower()):
            return model

    return None

def get_user_from_http_request(request):
    username = request.session.get(constants.SESSION_VARS['gatorlink'])
    user = User.objects.get(username=username)
    return user

def extract_model(model, filter_field, filter_value):
    """
    This function returns a single model object matching the the filter field and value
    If more than one model matches, it will return None

    Keyword arguments:
    model -- the name of the model
    filter_field -- the name of the field filtering on
    filter_value -- the value to search for given the field
    """

    try:
        return model.objects.get(**{filter_field: filter_value})
    except MultipleObjectsReturned:
        return None
    except model.DoesNotExist:
        return None

def Model_for_model(model):
    """
    Returns the capital M Model for a given instance
    """
    return type(model)
