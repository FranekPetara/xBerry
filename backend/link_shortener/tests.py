from unittest.mock import MagicMock, patch

import pytest
from django.urls import reverse
from link_shortener.models import Link
from link_shortener.tasks import create_shortened_link, get_last_three_links
from rest_framework import status
from rest_framework.test import APIClient

url = 'http://localhost:8000/api/shorten/'


@pytest.mark.django_db
def test_shorten_link_api_link_exists():
    client = APIClient()
    original_url = "https://pl.wikipedia.org/wiki/Wikipedia:Strona_g%C5%82%C3%B3wna"
    Link.objects.create(original_url=original_url, short_url="http://short.com/123")

    data = {'original_url': original_url}
    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_shorten_link_api_success():
    client = APIClient()

    data = {'original_url': "https://pl.wikipedia.org/wiki/Wikipedia:Strona_g%C5%82%C3%B3wna"}

    response = client.post(url, data, format='json')

    assert response.status_code == status.HTTP_201_CREATED

@pytest.mark.django_db
def test_shorten_link_api_view_invalid_data():
    client = APIClient()
    data = {'invalid_field': 'invalid_value'}

    response = client.post(url, data, format='json')

    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_create_shortened_link():
    # Przygotowanie danych testowych
    original_url = "http://example.com"
    
    # Wywołanie funkcji
    short_url = create_shortened_link(original_url)
    
    # Sprawdzenie czy link został stworzony
    link = Link.objects.filter(original_url=original_url).first()
    assert link is not None
    assert link.short_url == short_url


@pytest.mark.django_db
def test_get_last_three_links():
    original_urls = ["http://example1.com", "http://example2.com", "http://example3.com"]
    for original_url in original_urls:
        create_shortened_link(original_url)
    
    last_three_links = get_last_three_links()
    
    assert len(last_three_links) == 3
    assert last_three_links[0]['original_url'] == original_urls[-1]
    assert last_three_links[1]['original_url'] == original_urls[-2]
    assert last_three_links[2]['original_url'] == original_urls[-3]



# tutaj daje mocka. teoretycznie wszystkie testy powinny być wolne od zależności infrastruktury projektu
# jednak tutaj wszystko bym musial zastosować mock i to już gubi sens testów. 

@pytest.mark.django_db
@patch('link_shortener.tasks.create_shortened_link.delay')
@patch('link_shortener.tasks.get_last_three_links.delay')
def test_shorten_link_api_view(mock_get_last_three_links, mock_create_shortened_link):
    # Mocking celery tasks
    mock_shortened_link_result = MagicMock()
    mock_shortened_link_result.get.return_value = 'shortened_link'
    mock_last_three_links_result = MagicMock()
    mock_last_three_links_result.get.return_value = ['link1', 'link2', 'link3']
    mock_create_shortened_link.return_value = mock_shortened_link_result
    mock_get_last_three_links.return_value = mock_last_three_links_result

    # Prepare test data
    data = {'original_url': 'http://example.com/'}
    client = APIClient()

    # Make POST request to API endpoint
    url = reverse('shorten_link')
    response = client.post(url, data, format='json')
    print(response)

    # Assertions
    assert response.status_code == 201
    assert response.data['short_url'] == 'shortened_link'
    assert response.data['last_three_links'] == ['link1', 'link2', 'link3']

    # Check if celery tasks were called with correct arguments
    mock_create_shortened_link.assert_called_once_with('http://example.com/')
    mock_get_last_three_links.assert_called_once()

