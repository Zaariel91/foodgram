from rest_framework import viewsets, status
from djoser.views import UserViewSet
from recipes.models import (Tag, Ingredient, Recipe, Favorite,
                            ShopCart, IngredientsInRecipe)
from users.models import User, Subscribe
from api.serializers import (
    TagSerializer,
    IngredientSerializer,
    RecipeSerializer,
    UserCreateSerializer,
    CreateUpdateRecipeSerializer,
    SubscribeSerializer,
    FavoriteShopCartSerializer,
)
from api.permissions import IsAdminOrReadOnly
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from api.paginations import LimitPageNumberPagination
from django.http.response import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from api.filters import IngredientFilter, RecipeFilter
from django.db.models import Sum, F


class UserViewSet(UserViewSet):
    pagination_class = LimitPageNumberPagination

    @action(
        methods=['get'],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path='subscriptions',
        url_name='subscriptions',
    )
    def subscriptions(self, request):
        user = request.user
        queryset = Subscribe.objects.filter(user=user)
        pages = self.paginate_queryset(queryset)
        serializer = SubscribeSerializer(
            pages,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        methods=['post'],
        detail=True,
        permission_classes=[IsAuthenticated],
        url_path='subscribe',
        url_name='subscribe',
    )
    def subscribe(self, request, id=None):
        user = request.user
        author = get_object_or_404(User, id=id)
        if user == author:
            return Response(
                {'errors': 'Вы не можете подписаться сами на себя.'},
                status=status.HTTP_400_BAD_REQUEST)
        if Subscribe.objects.filter(user=user, author=author).exists():
            return Response(
                {'errors': 'Вы уже подписаны на данного пользователя.'},
                status=status.HTTP_400_BAD_REQUEST)
        subscriber = Subscribe.objects.create(user=user, author=author)
        serializer = SubscribeSerializer(
            subscriber, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def delete_subscribe(self, request, id=None):
        user = request.user
        author = get_object_or_404(User, id=id)
        subscriber = Subscribe.objects.filter(user=user, author=author)
        if subscriber.exists():
            subscriber.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({
            'errors': 'Подписка удалена.'
        })


class TagUserCreateViewset(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = [IsAdminOrReadOnly]


class TagViewset(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAdminOrReadOnly]


class IngredientViewset(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter


class RecipeViewset(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = LimitPageNumberPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ('create', 'partial_update'):
            return CreateUpdateRecipeSerializer
        return RecipeSerializer

    @action(
        methods=['post'],
        detail=True,
        permission_classes=[IsAuthenticated],
        url_path='shopping_cart',
        url_name='shopping_cart',
    )
    def shopping_cart(self, request, pk):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        if ShopCart.objects.filter(user=user, recipe=recipe).exists():
            return Response(
                {'errors': 'Рецепт уже добавлен в корзину.'},
                status=status.HTTP_400_BAD_REQUEST)
        ShopCart.objects.create(user=user, recipe=recipe)
        serializer = FavoriteShopCartSerializer(
            recipe,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        shop = ShopCart.objects.filter(user=user, recipe=recipe)
        if shop.exists():
            shop.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({
            'errors': 'Рецепт уже удален из корзины.'
        })

    @action(
        methods=['post'],
        detail=True,
        permission_classes=[IsAuthenticated],
        url_path='favorite',
        url_name='favorite',
    )
    def favorite(self, request, pk):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        if Favorite.objects.filter(user=user, recipe=recipe).exists():
            return Response(
                {'errors': 'Вы уже добавили рецепт в избранное.'},
                status=status.HTTP_400_BAD_REQUEST)
        Favorite.objects.create(user=user, recipe=recipe)
        serializer = FavoriteShopCartSerializer(recipe,
                                                context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        favorite = Favorite.objects.filter(user=user, recipe=recipe)
        if favorite.exists():
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({
            'errors': 'Рецепт уже удален из избранного.'
        })

    @action(
        methods=['get'],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path='download_shopping_cart',
        url_name='download_shopping_cart',
    )
    def download_shopping_cart(self, request):
        user = request.user
        if not user.shopping_carts.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        ingredients = IngredientsInRecipe.objects.filter(
            recipe__shopping_carts__user=user
        ).values('ingredients__name',
                 'ingredients__measurement_unit').annotate(
            name=F('ingredients__name'),
            unit=F('ingredients__measurement_unit'),
            total_amount=Sum('amount')
        )
        shop_cart = '\r\n'.join(
            [(f"{ing['name']}: {ing['total_amount']} {ing['unit']} ")
             for ing in ingredients]
        )
        response = HttpResponse(shop_cart, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="shop.txt"'
        return response
