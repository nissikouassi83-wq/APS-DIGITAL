from getpass import getpass

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create a non-administrator account for the protected dashboard."

    def handle(self, *args, **options):
        user_model = get_user_model()
        username = input("Identifiant : ").strip()
        if not username:
            raise CommandError("L’identifiant ne peut pas être vide.")
        if user_model.objects.filter(username=username).exists():
            raise CommandError(f"L’identifiant « {username} » existe déjà.")

        password = getpass("Mot de passe : ")
        confirmation = getpass("Confirmez le mot de passe : ")
        if password != confirmation:
            raise CommandError("Les deux mots de passe ne correspondent pas.")

        user = user_model(username=username)
        try:
            validate_password(password, user)
        except ValidationError as error:
            raise CommandError("; ".join(error.messages)) from error

        user_model.objects.create_user(username=username, password=password)
        self.stdout.write(self.style.SUCCESS(f"Compte « {username} » créé."))
