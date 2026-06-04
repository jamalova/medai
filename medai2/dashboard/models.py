from django.db import models


class Dataset(models.Model):
    name = models.CharField(max_length=200)
    file_size_mb = models.FloatField()
    row_count = models.IntegerField()
    columns = models.IntegerField()
    data_type = models.CharField(max_length=100)
    character_set = models.CharField(max_length=20, default='UTF-8')
    uploaded_by = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=20)
    article_count = models.IntegerField(default=0)

    @property
    def percentage(self):
        total = Category.objects.aggregate(models.Sum('article_count'))['article_count__sum'] or 1
        return round((self.article_count / total) * 100, 1)

    def __str__(self):
        return self.name


class ProcessingLog(models.Model):
    STATUS_CHOICES = [
        ('verified', 'Verified'),
        ('needs_review', 'Needs Review'),
        ('failed', 'Failed'),
    ]
    article_id = models.CharField(max_length=50)
    domain = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    confidence = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.article_id} - {self.status}"


class ModelMetrics(models.Model):
    total_articles = models.IntegerField()
    model_accuracy = models.FloatField()
    f1_score = models.FloatField()
    ai_confidence = models.CharField(max_length=20)
    cohesion = models.FloatField()
    overlap = models.FloatField()
    entropy = models.FloatField()
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-recorded_at']
        verbose_name_plural = 'Model Metrics'

    def __str__(self):
        return f"Metrics at {self.recorded_at}"
