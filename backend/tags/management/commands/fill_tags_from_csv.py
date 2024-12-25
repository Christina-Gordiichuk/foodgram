from django.core.management.base import BaseCommand, CommandError
from tags.models import Tag
from backend.settings import BASE_DIR
from django.db.utils import IntegrityError


class Command(BaseCommand):
    help = "Fills the table with the data from csv file"

    def handle(self, *args, **options):
        with open(BASE_DIR.parent / 'data/tags.csv', 'r') as csv_file:
            lines = csv_file.readlines()
            for line in lines:
                data = line.split(',')
                try:
                    ingr = Tag.objects.create(name=data[0].strip(), slug=data[0].strip())
                    ingr.save()
                except IntegrityError:
                    continue
                except Exception as e:
                    raise e

                self.stdout.write(
                    self.style.SUCCESS('Successfully wrote "%s"' % (data[0]))
                )