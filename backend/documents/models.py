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


# ---------------------------------------------------------------------------
# TODO: Define your own models for Questions and Answers.
#
# Here's a skeleton to get you thinking — feel free to change everything:
#
# class Question(models.Model):
#     """A single question extracted from an RFP document."""
#     rfp_document = models.ForeignKey(RFPDocument, on_delete=models.CASCADE, related_name="questions")
#     text = models.TextField()
#     order = models.PositiveIntegerField(default=0)
#
#     class Meta:
#         ordering = ["order"]
#
#     def __str__(self):
#         return self.text[:80]
#
#
# class Answer(models.Model):
#     """A generated answer to an RFP question."""
#     question = models.OneToOneField(Question, on_delete=models.CASCADE, related_name="answer")
#     content = models.TextField()
#     # TODO: Consider adding fields like:
#     #   - status (draft, approved, rejected)
#     #   - confidence_score
#     #   - source_documents (M2M to Document)
#     #   - generated_at
#     created_at = models.DateTimeField(auto_now_add=True)
#
#     def __str__(self):
#         return f"Answer to: {self.question.text[:50]}"
# ---------------------------------------------------------------------------
