from recipes.models import Ingredient
import csv


def run():
    with open('data/ingredients.csv', encoding="utf-8") as file:
        reader = csv.reader(file)
        next(reader)

        Ingredient.objects.all().delete()

        for row in reader:
            print(row)

            ingredients = Ingredient(
                name=row[0],
                measurement_unit=row[1])
            ingredients.save()
