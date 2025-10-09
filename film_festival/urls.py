from django.urls import path
from .views import FilmsToWatchList, FilmsWatchedList, RatingCreate, IncreaseUpVotes, MarkAsWatched, UserRatedFilmsList, UserUpvotedFilmsList, GenreList, DeleteProposedFilm, DeleteVote, EventCreateList, ProposeFilmView, EventFilmUpVote, DeleteEventFilmProposal, AdminEventDetail


urlpatterns = [
    path('films-to-watch/', FilmsToWatchList.as_view()),

    path('delete-film/<int:film_id>/', DeleteProposedFilm.as_view()),
    path('delete-vote/<int:film_id>/', DeleteVote.as_view()),
    
    path('films-watched/', FilmsWatchedList.as_view()),

    path('user-upvoted-films/', UserUpvotedFilmsList.as_view()),
    path('increase-up-votes/<int:film_id>/', IncreaseUpVotes.as_view()),

    path('genres/', GenreList.as_view()),

    path('mark-as-watched/<int:film_id>/', MarkAsWatched.as_view()),
    
    path('user-rated-films/', UserRatedFilmsList.as_view()),
    path('create-rating/<int:film_id>/', RatingCreate.as_view()),

    path('events/', EventCreateList.as_view(), name='events'),
    path('events/<int:event_id>/', AdminEventDetail.as_view(), name='event-detail'),
    path('events/<int:event_id>/propose-film/', ProposeFilmView.as_view(), name='propose-film'),
    path('events/upvote/<int:event_film_id>/', EventFilmUpVote.as_view(), name='event-film-upvote'),
    path('events/delete-proposed-film/<int:event_film_id>/', DeleteEventFilmProposal.as_view(), name='delete-event-film-proposal'),

]
