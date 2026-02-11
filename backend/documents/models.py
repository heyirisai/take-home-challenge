from django.db import models


class Document(models.Model):
    """A company knowledge-base document used to answer RFP questions."""

    title = models.CharField(max_length=255)
    content = models.TextField()
    file_name = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return self.title


class RFPDocument(models.Model):
    """An uploaded RFP document containing questions to be answered."""

    title = models.CharField(max_length=255)
    content = models.TextField()
    file_name = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return self.title
