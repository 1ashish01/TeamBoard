from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.db import transaction
from django.db.models import Q, Count
from rest_framework.permissions import IsAuthenticated

from .serializers import RegisterSerializer, LoginSerializer
from .models import KBEntry, QueryLog

from .permissions import IsAdminUser


class RegisterView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        user = serializer.save()
        company = user.company

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "username": user.username,
                "company_name": company.company_name,
                "api_key": company.api_key,
                "access": str(refresh.access_token),
            },
            status=status.HTTP_201_CREATED
        )


class LoginView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]

        user = authenticate(
            username=username,
            password=password
        )

        if user is None:
            return Response(
                {"detail": "Invalid username or password."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        company = user.company
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "access": str(refresh.access_token),
                "company_name": company.company_name,
                "api_key": company.api_key,
            },
            status=status.HTTP_200_OK
        )


class KBQueryView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        search_term = request.data.get("search", "").strip()

        if not search_term:
            return Response(
                {"detail": "Search term is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        company = request.user.company

        with transaction.atomic():
            entries = KBEntry.objects.filter(
                Q(question__icontains=search_term) |
                Q(answer__icontains=search_term)
            )

            count = entries.count()

            QueryLog.objects.create(
                company=company,
                search_term=search_term,
                results_count=count
            )

            results = [
                {
                    "id": str(entry.id),
                    "question": entry.question,
                    "answer": entry.answer,
                    "category": entry.category,
                }
                for entry in entries
            ]

        return Response(
            {
                "search": search_term,
                "count": count,
                "results": results,
            },
            status=status.HTTP_200_OK
        )
class AdminUsageSummaryView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        total_queries = QueryLog.objects.aggregate(
            total=Count('id')
        )['total']

        active_companies = QueryLog.objects.values(
            'company'
        ).distinct().count()

        top_terms = QueryLog.objects.values(
            'search_term'
        ).annotate(
            count=Count('id')
        ).order_by('-count')[:5]

        return Response(
            {
                "total_queries": total_queries,
                "active_companies": active_companies,
                "top_search_terms": list(top_terms),
            },
            status=status.HTTP_200_OK
        )