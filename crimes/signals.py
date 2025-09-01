from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Evidence
from .services import log_action


@receiver(post_save, sender=Evidence)
def evidence_created(sender, instance: Evidence, created, **kwargs):
    if created:
        user = instance.collected_by
        log_action(user, instance, "create_evidence", details=f"Code={instance.code}")
