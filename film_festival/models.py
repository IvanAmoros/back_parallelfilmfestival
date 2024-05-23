from django.db import models
from django.db.models import Avg
from django.contrib.auth.models import User

class Provider(models.Model):
    name = models.CharField(max_length=100)
    image_url = models.URLField(max_length=500)

    def __str__(self):
        return self.name
    

class Genre(models.Model):
    name = models.CharField(max_length=100)

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
    genre = models.CharField(max_length=250, blank=True, null=True)
    director = models.CharField(max_length=250, blank=True, null=True)
    actors = models.CharField(max_length=250, blank=True, null=True)
    imdb_rating = models.CharField(max_length=10, blank=True, null=True)
    imdb_votes = models.CharField(max_length=20, blank=True, null=True)
    imdb_id = models.CharField(max_length=20, blank=True, null=True, unique=True)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    proposed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='proposed_films')
    providers = models.ManyToManyField(Provider, related_name='films')
    genres = models.ManyToManyField(Genre, related_name='genres')


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
    

# class Comment(models.Model):
#     film = models.ForeignKey(
#         Film,
#         on_delete=models.CASCADE,
#     )
#     text = models.CharField(max_length=250)
#     updated = models.DateTimeField(auto_now=True)
#     created = models.DateTimeField(auto_now_add=True)
