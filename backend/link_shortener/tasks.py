import os
import uuid

from celery import shared_task

from .models import Link


@shared_task
def create_shortened_link(original_url):
    link = Link.objects.filter(original_url=original_url).first()
    if link:
        return link.short_url
    
    short_url_base = os.environ.get("SHORT_URL")
    unique_id = uuid.uuid4()
    short_url = f'{short_url_base}{unique_id}'
    link = Link.objects.create(original_url=original_url, short_url=short_url)
    return link.short_url

@shared_task
def get_last_three_links():
    last_three_links = Link.objects.order_by('-created_at')[:3]
    
    return [{'original_url': item.original_url, 'short_url': item.short_url} for item in last_three_links]

