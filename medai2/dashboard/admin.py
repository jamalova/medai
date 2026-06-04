from django.contrib import admin
from .models import Dataset, Category, ProcessingLog, ModelMetrics

@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    list_display = ['name', 'file_size_mb', 'row_count', 'uploaded_by', 'created_at']

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'article_count', 'color']

@admin.register(ProcessingLog)
class ProcessingLogAdmin(admin.ModelAdmin):
    list_display = ['article_id', 'domain', 'confidence', 'status', 'created_at']

@admin.register(ModelMetrics)
class ModelMetricsAdmin(admin.ModelAdmin):
    list_display = ['total_articles', 'model_accuracy', 'ai_confidence', 'recorded_at']
