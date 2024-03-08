from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import LinkSerializer
from .tasks import create_shortened_link, get_last_three_links


class ShortenLinkAPIView(APIView):
    def post(self, request):
        try:
            serializer = LinkSerializer(data=request.data)
            serializer.is_valid(raise_exception=True) 

            original_url = serializer.validated_data['original_url']
            
            short_url_result = create_shortened_link.delay(original_url)
            short_url = short_url_result.get()

            last_three_links_result = get_last_three_links.delay()
            last_three_links = last_three_links_result.get()

            response_data = {
                'short_url': short_url,
                'last_three_links': last_three_links
            }
            return Response(response_data, status=status.HTTP_201_CREATED)

        except Exception as e:
            print(str(e))
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


