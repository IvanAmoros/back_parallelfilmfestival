from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404
from rest_framework import status
from django.utils import timezone
from django.db import IntegrityError
from rest_framework.generics import ListCreateAPIView
from rest_framework.decorators import action
from rest_framework import viewsets

from .models import Film, Rating, Upvote, Provider, Genre, Event, EventFilm, EventFilmUpvote
from .serializers import FilmToWatchSerializer, FilmWatchedSerializer, RatingSerializer, GenreSerializer, EventSerializer, EventFilmSerializer, EventEditSerializer


class DeleteProposedFilm(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, film_id, format=None):
        film = get_object_or_404(Film, pk=film_id)
        if film.watched:
            return Response({'detail': 'Film already marked as watched and cannot be deleted.'}, status=status.HTTP_400_BAD_REQUEST)
        if film.proposed_by != request.user:
            return Response({'detail': 'You do not have permission to delete this film.'}, status=status.HTTP_403_FORBIDDEN)
        film.delete()
        return Response({'detail': 'Film deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)
    

class DeleteVote(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, film_id, format=None):
        user = request.user
        film = get_object_or_404(Film, pk=film_id)
        upvote = Upvote.objects.filter(user=user, film=film).first()

        if not upvote:
            return Response({'detail': 'You have not upvoted this film.'}, status=status.HTTP_400_BAD_REQUEST)

        upvote.delete()
        film.total_upvotes -= 1
        film.save()

        return Response({'detail': 'Vote deleted successfully.'}, status=status.HTTP_200_OK)


class FilmsToWatchList(ListAPIView):
    serializer_class = FilmToWatchSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            self.permission_classes = [AllowAny]
        elif self.request.method == 'POST':
            self.permission_classes = [IsAuthenticated]
        return super(FilmsToWatchList, self).get_permissions()

    def get_queryset(self):
        queryset = Film.objects.filter(watched=False).order_by('-total_upvotes', 'created')
        genres = self.request.query_params.getlist('genres')
        if genres:
            genre_objects = Genre.objects.filter(name__in=genres)
            queryset = queryset.filter(genres__in=genre_objects).distinct()
        return queryset

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            imdb_id = serializer.validated_data.get('imdb_id')
            if not imdb_id:
                return Response({'detail': 'The IMDb ID is required.'}, status=status.HTTP_400_BAD_REQUEST)
            if Film.objects.filter(imdb_id=imdb_id).exists():
                return Response({'detail': 'This movie has already been proposed.'}, status=status.HTTP_400_BAD_REQUEST)
            try:
                film = serializer.save(proposed_by=request.user)
                providers_data = request.data.get('providers', [])
                for provider_data in providers_data:
                    provider, created = Provider.objects.get_or_create(
                        name=provider_data['name'],
                        defaults={'image_url': provider_data['image_url']}
                    )
                    film.providers.add(provider)
                genres_data = request.data.get('genres', [])
                for genre_name in genres_data:
                    genre, created = Genre.objects.get_or_create(name=genre_name)
                    film.genres.add(genre)
                Upvote.objects.create(user=request.user, film=film)
                film.total_upvotes += 1
                film.save()
                return Response(FilmToWatchSerializer(film).data, status=status.HTTP_201_CREATED)
            except IntegrityError:
                return Response({'detail': 'This movie has already been proposed.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class FilmsWatchedList(ListAPIView):
    queryset = Film.objects.filter(watched=True).order_by('-watched_date')
    serializer_class = FilmWatchedSerializer
    permission_classes = [AllowAny]


class GenreList(ListAPIView):
    queryset = Genre.objects.filter().order_by('name')
    serializer_class = GenreSerializer
    permission_classes = [AllowAny]


class RatingCreate(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, film_id, format=None):
        film = get_object_or_404(Film, pk=film_id)
        user = request.user

        existing_rating = Rating.objects.filter(film=film, user=user).first()
        if existing_rating:
            return Response({'detail': 'You have already rated this film.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = RatingSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(film=film, user=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserRatedFilmsList(ListAPIView):
    serializer_class = FilmWatchedSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        rated_films_ids = Rating.objects.filter(user=user).values_list('film_id', flat=True)
        return Film.objects.filter(id__in=rated_films_ids)


class UserUpvotedFilmsList(ListAPIView):
    serializer_class = FilmToWatchSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        upvoted_films_ids = Upvote.objects.filter(user=user).values_list('film_id', flat=True)
        return Film.objects.filter(id__in=upvoted_films_ids)


class IncreaseUpVotes(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, film_id):
        user = request.user
        film = get_object_or_404(Film, pk=film_id)

        if Upvote.objects.filter(user=user, film=film).exists():
            return Response({'detail': 'You have already upvoted this film.'}, status=status.HTTP_400_BAD_REQUEST)

        Upvote.objects.create(user=user, film=film)

        film.total_upvotes += 1
        film.save()

        return Response({'total_upvotes': film.total_upvotes}, status=status.HTTP_200_OK)


class MarkAsWatched(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, film_id):
        film = Film.objects.get(pk=film_id)
        if not film.watched:
            film.watched = True
            film.watched_date = timezone.now()
            film.save()
            return Response({'status': 'Film marked as watched', 'watched_date': film.watched_date}, status=status.HTTP_200_OK)
        return Response({'error': 'Film already marked as watched'}, status=status.HTTP_400_BAD_REQUEST)
    
class EventCreateList(ListCreateAPIView):
    queryset = Event.objects.all().order_by('date')
    serializer_class = EventSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            self.permission_classes = [AllowAny]
        else:  # POST
            self.permission_classes = [IsAdminUser]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class AdminEventDetail(APIView):
    permission_classes = [IsAdminUser]

    def get_object(self, event_id):
        return get_object_or_404(Event, pk=event_id)

    # Editar evento
    def put(self, request, event_id):
        event = self.get_object(event_id)
        serializer = EventEditSerializer(event, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'detail': 'Evento actualizado correctamente.', 'event': serializer.data}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Eliminar evento
    def delete(self, request, event_id):
        event = self.get_object(event_id)
        event.delete()
        return Response({'detail': 'Evento eliminado correctamente.'}, status=status.HTTP_204_NO_CONTENT)


class ProposeFilmView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, event_id):
        event = get_object_or_404(Event, pk=event_id)

        if not event.allow_proposals:
            return Response({'detail': 'Este evento no permite propuestas.'}, status=status.HTTP_403_FORBIDDEN)

        imdb_id = request.data.get('imdb_id')
        if not imdb_id:
            return Response({'detail': 'IMDb ID requerido.'}, status=status.HTTP_400_BAD_REQUEST)

        film, created = Film.objects.get_or_create(
            imdb_id=imdb_id,
            defaults={
                'tittle': request.data.get('tittle', ''),
                'description': request.data.get('description', ''),
                'year': request.data.get('year', 0),
                'runtime': request.data.get('runtime', ''),
                'image': request.data.get('image', ''),
                'director': request.data.get('director', ''),
                'actors': request.data.get('actors', ''),
                'imdb_rating': request.data.get('imdb_rating', ''),
                'imdb_votes': request.data.get('imdb_votes', ''),
                # 'proposed_by': request.user
            }
        )

        # 🔁 Si la película ya existía, actualiza los campos vacíos con datos nuevos
        if not created:
            updated_fields = []
            for field in ['tittle', 'description', 'year', 'runtime', 'image', 'director', 'actors', 'imdb_rating', 'imdb_votes']:
                new_value = request.data.get(field)
                if new_value and not getattr(film, field):
                    setattr(film, field, new_value)
                    updated_fields.append(field)
            if updated_fields:
                film.save(update_fields=updated_fields)

        # ⚙️ Procesar proveedores
        providers_data = request.data.get('providers', [])
        for provider_data in providers_data:
            provider, _ = Provider.objects.get_or_create(
                name=provider_data['name'],
                defaults={'image_url': provider_data.get('image_url', '')}
            )
            film.providers.add(provider)

        # ⚙️ Procesar géneros
        genres_data = request.data.get('genres', [])
        for genre_name in genres_data:
            genre, _ = Genre.objects.get_or_create(name=genre_name)
            film.genres.add(genre)

        # ⚙️ Verificar que no esté ya propuesta en este evento
        if EventFilm.objects.filter(event=event, film=film).exists():
            return Response({'detail': 'Esta película ya ha sido propuesta en este evento.'}, status=status.HTTP_400_BAD_REQUEST)

        # ⚙️ Crear relación en el evento
        event_film, created = EventFilm.objects.get_or_create(
            event=event, film=film,
            defaults={'proposed_by': request.user}
        )

        # ⚙️ Registrar el voto del usuario si no existía
        event_film_upvote, created_vote = EventFilmUpvote.objects.get_or_create(
            event_film=event_film, user=request.user
        )

        # ⚙️ Si el voto es nuevo, sumamos +1 al contador
        if created_vote:
            event_film.upvote_count += 1
            event_film.save()

        film.save()

        return Response({'detail': 'Película propuesta correctamente.'}, status=status.HTTP_201_CREATED)
    

class DeleteEventFilmProposal(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, event_film_id, format=None):
        user = request.user
        event_film = get_object_or_404(EventFilm, pk=event_film_id)

        # Solo el usuario que propuso la película puede borrarla
        if event_film.proposed_by != user:
            return Response(
                {'detail': 'No tienes permiso para eliminar esta propuesta.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Eliminar la relación (no la película original)
        event_film.delete()
        return Response(
            {'detail': 'Propuesta de película eliminada correctamente.'},
            status=status.HTTP_204_NO_CONTENT
        )


class EventFilmUpVote(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, event_film_id):
        user = request.user
        event_film = get_object_or_404(EventFilm, pk=event_film_id)

        if EventFilmUpvote.objects.filter(user=user, event_film=event_film).exists():
            return Response({'detail': 'Ya has votado esta película en este evento.'}, status=status.HTTP_400_BAD_REQUEST)

        EventFilmUpvote.objects.create(user=user, event_film=event_film)

        event_film.upvote_count += 1
        event_film.save()

        return Response({'upvote_count': event_film.upvote_count}, status=status.HTTP_200_OK)
    
    def delete(self, request, event_film_id, format=None):
        user = request.user
        event_film = get_object_or_404(EventFilm, pk=event_film_id)
        upvote = EventFilmUpvote.objects.filter(user=user, event_film=event_film).first()

        if not upvote:
            return Response({'detail': 'No has votado esta película en este evento.'}, status=status.HTTP_400_BAD_REQUEST)

        upvote.delete()
        if event_film.upvote_count > 0:
            event_film.upvote_count -= 1
            event_film.save()

        return Response({'detail': 'Voto eliminado correctamente.'}, status=status.HTTP_200_OK)
