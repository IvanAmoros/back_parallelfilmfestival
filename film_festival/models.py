from django.db import models
from django.db.models import Avg
from django.contrib.auth.models import User

class Provider(models.Model):
    name = models.CharField(max_length=100)
    image_url = models.URLField(max_length=500)

    def __str__(self):
        return self.name
    

class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name
    

class Film(models.Model):
    tittle = models.CharField(max_length=250)
    image = models.CharField(max_length=250, null=True, blank=True)
    description = models.CharField(max_length=1000)
    watched = models.BooleanField(default=False)
    watched_date = models.DateField(null=True, blank=True)
    total_upvotes = models.IntegerField(default=0)
    year = models.IntegerField(default=0)
    runtime = models.CharField(max_length=50, blank=True, null=True)
    genres = models.ManyToManyField(Genre, related_name='genres')
    director = models.CharField(max_length=250, blank=True, null=True)
    actors = models.CharField(max_length=250, blank=True, null=True)
    imdb_rating = models.CharField(max_length=10, blank=True, null=True)
    imdb_votes = models.CharField(max_length=20, blank=True, null=True)
    imdb_id = models.CharField(max_length=20, blank=True, null=True, unique=True)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    proposed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='proposed_films')
    providers = models.ManyToManyField(Provider, related_name='films', blank=True)

    @property
    def average_rating(self):
        return self.ratings.filter(stars__isnull=False).aggregate(average=Avg('stars'))['average'] or 0

    def __str__(self):
        return self.tittle
    
    
class Upvote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_upvotes')
    film = models.ForeignKey(Film, on_delete=models.CASCADE, related_name='upvotes')

    class Meta:
        unique_together = ('user', 'film')

class Rating(models.Model):
    film = models.ForeignKey(
        Film,
        on_delete=models.CASCADE,
        related_name='ratings'
    )
    stars = models.IntegerField(null=True, choices=[(i, i) for i in range(1, 11)])
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings')

    def __str__(self):
        return self.film.tittle + ": " + str(self.stars)
    
class Event(models.Model):
    title = models.CharField(max_length=250)
    description = models.TextField(max_length=1000)
    date = models.DateField()
    meeting_hour = models.TimeField()
    start_hour = models.TimeField()
    allow_proposals = models.BooleanField(default=True)
    watched = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="created_events")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    proposed_films = models.ManyToManyField('Film', through='EventFilm', related_name='events')

    def __str__(self):
        return f"{self.title} ({self.date})"

class EventFilm(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    film = models.ForeignKey(Film, on_delete=models.CASCADE)
    proposed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    upvote_count = models.PositiveIntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('event', 'film')

    def __str__(self):
        return f"{self.film.tittle} @ {self.event.title}"
    
class EventFilmUpvote(models.Model):
    event_film = models.ForeignKey(EventFilm, on_delete=models.CASCADE, related_name='upvotes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('event_film', 'user')

    def __str__(self):
        return f"{self.user.username} → {self.event_film.film.tittle}"
