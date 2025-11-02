from django.views.generic import FormView

from hope_portal.ui.forms.flow import SMSForm


class SMSView(FormView[SMSForm]):
    form_class = SMSForm
    template_name = "pages/flow/open_issue.html"
