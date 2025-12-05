from django.views.generic import FormView

from hope_portal.ui.forms.flow import SMSForm


class IssueView(FormView[SMSForm]):
    pass
