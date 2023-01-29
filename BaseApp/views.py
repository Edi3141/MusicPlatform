import os
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, viewsets, parsers, views, filters, permissions, mixins
from . import models, serializers
from .MixedClass import MixedSerializer, Pagination
from .models import Genre, Track
from .permissions import IsAuthor
from .services import delete_old_file
from rest_framework.filters import SearchFilter
from rest_framework.viewsets import ModelViewSet


class Search(ModelViewSet):
    queryset = Track.objects.all()
    filter_backends = (SearchFilter,)
    search_fields = ('music_name',)
    serializer_class = serializers.SearchSerializer


class GenreView(generics.ListAPIView):
    queryset = models.Genre.objects.all()
    serializer_class = serializers.GenreSerializer


class LicenseView(viewsets.ModelViewSet):
    serializer_class = serializers.LicenseSerializer
    permission_classes = [IsAuthor]

    def get_queryset(self):
        return models.License.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AlbumView(viewsets.ModelViewSet):
    parser_classes = (parsers.MultiPartParser,)
    serializer_class = serializers.AlbumSerializer
    permission_classes = [IsAuthor]

    def get_queryset(self):
        return models.Album.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_destroy(self, instance):
        delete_old_file(instance.cover.path)
        instance.delete()


class PublicAlbumView(generics.ListAPIView):
    serializer_class = serializers.AlbumSerializer

    def get_queryset(self):
        return models.Album.objects.filter(user__id=self.kwargs.get('pk'), private=False)


class TrackViewSet(viewsets.ModelViewSet):
    queryset = Track.objects.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        print(self.action)
        if self.action == 'list':
            return serializers.TrackListSerializer
        elif self.action == 'retrieve':
            return serializers.TrackDetailSerializer
        return serializers.TrackSerializer

    def get_permissions(self):
        if self.action in ('update', 'partial_update', 'destroy'):
            return [permissions.IsAuthenticated(), IsAuthor()]
        return [permissions.IsAuthenticatedOrReadOnly(), ]


class PlayListView(MixedSerializer, viewsets.ModelViewSet):
    parser_classes = (parsers.MultiPartParser,)
    permission_classes = [IsAuthor]
    serializer_class = serializers.CreatePlayListSerializer
    serializer_classes_by_action = {
        'list': serializers.PlayListSerializer
    }

    def get_queryset(self):
        return models.PlayList.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_destroy(self, instance):
        delete_old_file(instance.cover.path)
        instance.delete()


class TrackListView(generics.ListAPIView):
    queryset = models.Track.objects.filter(album__private=False, private=False)
    serializer_class = serializers.AuthorTrackSerializer
    pagination_class = Pagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['music_name', 'album', 'genre']


class AuthorTrackListView(generics.ListAPIView):
    serializer_class = serializers.AuthorTrackSerializer
    pagination_class = Pagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['music_name', 'album', 'genre']

    def get_queryset(self):
        return models.Track.objects.filter(
            user__id=self.kwargs.get('pk'), album__private=False, private=False
        )


class CommentAuthorView(viewsets.ModelViewSet):
    serializer_class = serializers.CommentAuthorSerializer
    permission_classes = [IsAuthor]

    def get_queryset(self):
        return models.Comment.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CommentView(viewsets.ModelViewSet):
    serializer_class = serializers.CommentSerializer

    def get_queryset(self):
        return models.Comment.objects.filter(track_id=self.kwargs.get('pk'))


class StreamingFileView(views.APIView):

    def set_play(self):
        self.track.plays_count += 1
        self.track.save()

    def get(self, request, pk):
        self.track = get_object_or_404(models.Track, id=pk, private=False)
        if os.path.exists(self.track.file.path):
            self.set_play()
            response = HttpResponse('', content_type="audio/mpeg", status=206)
            response['X-Accel-Redirect'] = f"/mp3/{self.track.file.name}"
            return response
        else:
            return Http404


class DownloadTrackView(views.APIView):

    def set_download(self):
        self.track.download += 1
        self.track.save()

    def get(self, request, pk):
        self.track = get_object_or_404(models.Track, id=pk, private=False)
        if os.path.exists(self.track.file.path):
            self.set_download()
            response = HttpResponse('', content_type="audio/mpeg", status=206)
            response["Content-Disposition"] = f"attachment; filename={self.track.file.name}"
            response['X-Accel-Redirect'] = f"/media/{self.track.file.name}"
            return response
        else:
            return Http404


class StreamingFileAuthorView(views.APIView):

    permission_classes = [IsAuthor]

    def get(self, request, pk):
        self.track = get_object_or_404(models.Track, id=pk, user=request.user)
        if os.path.exists(self.track.file.path):
            response = HttpResponse('', content_type="audio/mpeg", status=206)
            response['X-Accel-Redirect'] = f"/mp3/{self.track.file.name}"
            return response
        else:
            return Http404
