from django.test import TestCase
from rest_framework.test import APITestCase

from .models import Document, RFPDocument


class DocumentModelTest(TestCase):
    def test_create_document(self):
        doc = Document.objects.create(
            title="Test Document",
            content="Test content",
            file_name="test.txt",
        )
        self.assertEqual(str(doc), "Test Document")


class RFPDocumentModelTest(TestCase):
    def test_create_rfp_document(self):
        rfp = RFPDocument.objects.create(
            title="Test RFP",
            content="Test RFP content",
            file_name="test_rfp.txt",
        )
        self.assertEqual(str(rfp), "Test RFP")


class DocumentAPITest(APITestCase):
    def test_list_documents(self):
        response = self.client.get("/api/documents/")
        self.assertEqual(response.status_code, 200)

    def test_create_document(self):
        data = {"title": "New Doc", "content": "Some content"}
        response = self.client.post("/api/documents/", data)
        self.assertEqual(response.status_code, 201)
