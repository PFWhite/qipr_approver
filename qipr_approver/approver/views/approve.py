import json

from django.contrib.auth.decorators import login_required
from django.utils import timezone

from approver.forms import QuestionForm
from approver.workflows import project_crud, approve_workflow

import approver.utils as utils

@login_required
def approve(request, project_id=None):
    context = {
        'content': 'approver/approve.html',
        'project_id': project_id,
        'toast_text': utils.get_and_reset_toast(request.session)
    }
    current_user = request.user 
    if request.method == 'POST':
        question_form = request.POST
        project = project_crud.get_project_or_none(project_id)
        project = approve_workflow.save_project_with_form(project, question_form, request)

        request.access_log.model = project

        return approve_workflow.approve_or_next_steps(project, current_user)

    else:
        now = timezone.now()
        if(project_id):
            project = project_crud.get_project_or_none(project_id)
            if(project is None):
                return utils.dashboard_redirect_and_toast(request, 'Project with id {} does not exist.'.format(project_id))
            else:
                if(project_crud.is_current_project_editable(current_user,project)):
                    question_form = QuestionForm(project_id=project_id)
                    context['sorted_questions'] = question_form.get_random_questions()

                    return utils.layout_render(request, context)
                else:
                    return utils.dashboard_redirect_and_toast(request, 'You are not authorized to edit this project.')
        else:
            return utils.dashboard_redirect_and_toast(request, 'You need to have a project.')

