from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from faker import Faker
from crimes.models import Incident, Person


class Command(BaseCommand):
    help = "Generate demo data: incidents and persons."

    def add_arguments(self, parser):
        parser.add_argument("--incidents", type=int, default=5)
        parser.add_argument("--people", type=int, default=10)

    def handle(self, *args, **options):
        fake = Faker()
        User = get_user_model()
        reporter = User.objects.first()
        for _ in range(options["incidents"]):
            Incident.objects.create(
                title=fake.sentence(), description=fake.text(), reported_by=reporter
            )
        for _ in range(options["people"]):
            Person.objects.create(
                first_name=fake.first_name(), last_name=fake.last_name()
            )
        self.stdout.write(self.style.SUCCESS("Demo data generated"))
