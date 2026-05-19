from django.db import models


class Lead(models.Model):
    SOURCE_WEBSITE = 'website'
    SOURCE_GOOGLE_FORMS = 'google_forms'
    SOURCE_INSTAGRAM_ADS = 'instagram_ads'
    SOURCE_INSTAGRAM_DMS = 'instagram_dms'
    SOURCE_MANUAL = 'manual'

    SOURCE_CHOICES = [
        (SOURCE_WEBSITE, 'Website Form'),
        (SOURCE_GOOGLE_FORMS, 'Google Forms'),
        (SOURCE_INSTAGRAM_ADS, 'Instagram Ads'),
        (SOURCE_INSTAGRAM_DMS, 'Instagram DMs'),
        (SOURCE_MANUAL, 'Manual Entry'),
    ]

    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    service = models.CharField(max_length=100)
    budget = models.IntegerField()
    message = models.TextField()
    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default=SOURCE_WEBSITE,
    )
    external_id = models.CharField(max_length=255, blank=True, null=True)
    raw_data = models.JSONField(blank=True, null=True)

    def __str__(self):
        return self.name
