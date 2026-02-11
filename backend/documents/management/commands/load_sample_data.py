import os

from django.core.management.base import BaseCommand

from documents.models import Document, RFPDocument


class Command(BaseCommand):
    help = "Load sample company documents and RFP into the database"

    def handle(self, *args, **options):
        sample_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "sample_data")

        # Load company documents
        docs_dir = os.path.join(sample_dir, "documents")
        doc_count = 0
        for filename in sorted(os.listdir(docs_dir)):
            if not filename.endswith(".txt"):
                continue
            filepath = os.path.join(docs_dir, filename)
            with open(filepath, "r") as f:
                content = f.read()
            title = filename.replace("_", " ").replace(".txt", "").title()
            doc, created = Document.objects.get_or_create(
                file_name=filename,
                defaults={"title": title, "content": content},
            )
            if created:
                doc_count += 1
                self.stdout.write(f"  Created document: {title}")
            else:
                self.stdout.write(f"  Skipped (already exists): {title}")

        # Load sample RFP
        rfp_dir = os.path.join(sample_dir, "rfps")
        rfp_count = 0
        for filename in sorted(os.listdir(rfp_dir)):
            if not filename.endswith(".txt"):
                continue
            filepath = os.path.join(rfp_dir, filename)
            with open(filepath, "r") as f:
                content = f.read()
            title = filename.replace("_", " ").replace(".txt", "").title()
            rfp, created = RFPDocument.objects.get_or_create(
                file_name=filename,
                defaults={"title": title, "content": content},
            )
            if created:
                rfp_count += 1
                self.stdout.write(f"  Created RFP: {title}")
            else:
                self.stdout.write(f"  Skipped (already exists): {title}")

        self.stdout.write(
            self.style.SUCCESS(f"Done! Loaded {doc_count} documents and {rfp_count} RFPs.")
        )
