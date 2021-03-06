from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse

from wagtail_review.forms import ResponseForm
from wagtail_review.models import Response, Reviewer

SUCCESS_RESPONSE_MESSAGE = "Thank you, your review has been received."


def view(request, reviewer_id, token):
    reviewer = get_object_or_404(Reviewer, id=reviewer_id)
    if token != reviewer.view_token:
        raise PermissionDenied

    page = reviewer.review.page_revision.as_page_object()
    dummy_request = page.dummy_request(request)
    dummy_request.wagtailreview_mode = 'view'
    dummy_request.wagtailreview_reviewer = reviewer
    return page.serve_preview(dummy_request, page.default_preview_mode)


def respond(request, reviewer_id, token):
    reviewer = get_object_or_404(Reviewer, id=reviewer_id)
    if token != reviewer.response_token:
        raise PermissionDenied

    if request.method == 'POST':
        response = Response(reviewer=reviewer)
        form = ResponseForm(request.POST, instance=response)
        if form.is_valid() and reviewer.review.status != 'closed':
            form.save()
            response.send_notification_to_submitter()
            if request.user.has_perm('wagtailadmin.access_admin'):
                messages.success(request, SUCCESS_RESPONSE_MESSAGE)
                return redirect(reverse('wagtail_review_admin:dashboard'))
            return HttpResponse(SUCCESS_RESPONSE_MESSAGE)

    else:
        page = reviewer.review.page_revision.as_page_object()
        dummy_request = page.dummy_request(request)
        dummy_request.wagtailreview_mode = 'respond'
        dummy_request.wagtailreview_reviewer = reviewer
        return page.serve_preview(dummy_request, page.default_preview_mode)
