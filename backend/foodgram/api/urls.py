from rest_framework import routers
from django.urls import include, path
from api.views import TagViewset, IngredientViewset, RecipeViewset, UserViewSet


router = routers.DefaultRouter()

router.register(r'tags', TagViewset, basename='tags')
router.register(r'ingredients', IngredientViewset, basename='ingredients')
router.register(r'recipes', RecipeViewset, basename='recipes')
router.register(r'users', UserViewSet)


urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
