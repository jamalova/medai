from django.shortcuts import render
from django.http import JsonResponse
import os
from .models import Category, ProcessingLog, ModelMetrics, Dataset
from .search_engine import search_engine, tokenize, InvertedIndex


# ===========================================================
# DASHBOARD CONTEXT
# ===========================================================

def get_dashboard_context():
    categories = list(Category.objects.all().order_by('-article_count'))
    logs = ProcessingLog.objects.select_related('domain').order_by('-created_at')[:10]
    metrics = ModelMetrics.objects.first()
    dataset = Dataset.objects.first()

    if not metrics:
        metrics_data = {
            'total_articles': 5412,
            'model_accuracy': 94.5,
            'f1_score': 0.92,
            'ai_confidence': 'High',
            'cohesion': 0.89,
            'overlap': 4.2,
            'entropy': 1.34,
        }
    else:
        metrics_data = {
            'total_articles': metrics.total_articles,
            'model_accuracy': metrics.model_accuracy,
            'f1_score': metrics.f1_score,
            'ai_confidence': metrics.ai_confidence,
            'cohesion': metrics.cohesion,
            'overlap': metrics.overlap,
            'entropy': metrics.entropy,
        }

    if not categories:
        categories_data = [
            {'name': 'Cardiology', 'article_count': 1240, 'percentage': 23, 'color': '#3b6fd4'},
            {'name': 'Oncology', 'article_count': 982, 'percentage': 18, 'color': '#2ec27e'},
            {'name': 'Neurology', 'article_count': 756, 'percentage': 14, 'color': '#a347ba'},
            {'name': 'Pediatrics', 'article_count': 620, 'percentage': 11, 'color': '#7f6ab5'},
            {'name': 'Immunology', 'article_count': 512, 'percentage': 9, 'color': '#e5a50a'},
        ]
    else:
        categories_data = [
            {
                'name': c.name,
                'article_count': c.article_count,
                'percentage': c.percentage,
                'color': c.color,
            }
            for c in categories
        ]

    if not logs:
        logs_data = [
            {'article_id': 'PUB-9021-A', 'domain': 'Cardiology', 'confidence': 98, 'status': 'verified', 'time': '2 mins ago'},
            {'article_id': 'PUB-9022-X', 'domain': 'Oncology', 'confidence': 92, 'status': 'verified', 'time': '12 mins ago'},
            {'article_id': 'PUB-9023-R', 'domain': 'Neurology', 'confidence': 74, 'status': 'needs_review', 'time': '1 hour ago'},
        ]
    else:
        logs_data = [
            {
                'article_id': log.article_id,
                'domain': log.domain.name if log.domain else 'Unknown',
                'confidence': log.confidence,
                'status': log.status,
                'time': log.created_at.strftime('%H:%M'),
            }
            for log in logs
        ]

    if not dataset:
        dataset_data = {
            'name': 'clinical_studies_q1_24.xlsx',
            'file_size_mb': 12.4,
            'row_count': 5412,
            'columns': 24,
            'data_type': 'Semi-Structured',
            'character_set': 'UTF-8',
            'uploaded_by': 'Dr. Thorne',
            'days_ago': 4,
        }
    else:
        dataset_data = {
            'name': dataset.name,
            'file_size_mb': dataset.file_size_mb,
            'row_count': dataset.row_count,
            'columns': dataset.columns,
            'data_type': dataset.data_type,
            'character_set': dataset.character_set,
            'uploaded_by': dataset.uploaded_by,
            'days_ago': 4,
        }

    return {
        'metrics': metrics_data,
        'categories': categories_data,
        'logs': logs_data,
        'dataset': dataset_data,
        'total_categories': len(categories_data),
    }


# ===========================================================
# SAHIFA VIEWLARI
# ===========================================================

def dashboard(request):
    context = get_dashboard_context()
    context['active_page'] = 'dashboard'
    return render(request, 'dashboard/index.html', context)


def datasets(request):
    context = get_dashboard_context()
    context['active_page'] = 'datasets'
    return render(request, 'dashboard/index.html', context)


def classifier(request):
    context = {'active_page': 'classifier'}
    return render(request, 'dashboard/index.html', context)


def analytics(request):
    context = {'active_page': 'analytics'}
    return render(request, 'dashboard/index.html', context)


def api_logs(request):
    ctx = get_dashboard_context()
    return JsonResponse({'logs': ctx['logs']})


# ===========================================================
# QIDIRUV TIZIMI
# ===========================================================

def _build_search_index():
    """Demo data bilan indeks yaratadi."""
    if search_engine._is_built:
        return
    demo_docs = [
        (1, "Cardiology heart disease treatment clinical study patients"),
        (2, "Oncology cancer tumor treatment chemotherapy radiation"),
        (3, "Neurology brain stroke neural disorder treatment"),
        (4, "Pediatrics children disease vaccination growth"),
        (5, "Immunology immune system antibody infection virus"),
        (6, "yurak kasalligi davolash kardiologiya"),
        (7, "saraton onkologiya kimyoterapiya"),
        (8, "nevrologiya miya insult davolash"),
    ]
    for doc_id, text in demo_docs:
        search_engine.index_document(doc_id, text)
    search_engine._is_built = True
    
    from .search_engine import load_xlsx_to_engine
    res = load_xlsx_to_engine(search_engine, xlsx_path)
    
    if 'error' in res:
        print(f"[MEDAI Search] Xato: {res['error']}")
        # Fallback to demo
        demo_docs = [
            (1, "Cardiology heart disease treatment clinical study patients"),
            (2, "Oncology cancer tumor treatment chemotherapy radiation"),
            (3, "Neurology brain stroke neural disorder treatment"),
        ]
        for doc_id, text in demo_docs:
            search_engine.index_document(doc_id, text)
        search_engine._is_built = True
    else:
        print(f"[MEDAI Search] Muvaffaqiyatli yuklandi: {res['loaded']} hujjat")


def api_search(request):
    """
    BM25 yoki TF-IDF bilan qidiruv.
    GET /api/search/?q=so'rov&model=bm25&top_k=10
    """
    query = request.GET.get('q', '').strip()
    model = request.GET.get('model', 'bm25').lower()
    top_k = int(request.GET.get('top_k', 10))

    if not query:
        return JsonResponse({'error': "q parametrini kiriting"}, status=400)
    if model not in ('bm25', 'tfidf'):
        return JsonResponse({'error': "model 'bm25' yoki 'tfidf' bo'lishi kerak"}, status=400)

    _build_search_index()
    result = search_engine.search(query, model=model, top_k=top_k)
    return JsonResponse(result)


def api_search_compare(request):
    """
    TF-IDF va BM25 natijalarini solishtiradi.
    GET /api/search/compare/?q=so'rov&top_k=5
    """
    query = request.GET.get('q', '').strip()
    top_k = int(request.GET.get('top_k', 5))

    if not query:
        return JsonResponse({'error': "q parametrini kiriting"}, status=400)

    _build_search_index()
    result = search_engine.compare_models(query, top_k=top_k)
    return JsonResponse(result)


def api_tokenize(request):
    """
    Matnni tokenlarga ajratadi.
    GET /api/tokenize/?text=matn
    """
    text = request.GET.get('text', '').strip()

    if not text:
        return JsonResponse({'error': "text parametrini kiriting"}, status=400)

    tokens = tokenize(text)
    mini_index = InvertedIndex()
    mini_index.add_document(1, text)
    inverted_preview = {
        token: list(mini_index.index[token][1])
        for token in tokens
        if token in mini_index.index
    }

    return JsonResponse({
        'original': text,
        'tokens': tokens,
        'token_count': len(tokens),
        'inverted_index_preview': inverted_preview,
    })


def api_search_stats(request):
    """
    Indeks statistikasi.
    GET /api/search/stats/
    """
    _build_search_index()
    stats = search_engine.get_index_stats()
    return JsonResponse({
        'index_stats': stats,
        'models_available': ['TF-IDF', 'BM25'],
    })


def api_tokens(request):
    """
    Token chastotalari.
    GET /api/tokens/?limit=100
    """
    _build_search_index()
    limit = int(request.GET.get('limit', 100))
    tokens = search_engine.get_token_frequencies(limit=limit)
    return JsonResponse({'tokens': tokens})


def api_inverted_index(request):
    """
    Teskari indeks namunasi.
    GET /api/inverted-index/?limit=50
    """
    _build_search_index()
    limit = int(request.GET.get('limit', 50))
    sample = search_engine.get_inverted_index_sample(limit=limit)
    return JsonResponse({'inverted_index': sample})


def api_slots(request):
    """
    Slot extraction namunasi.
    GET /api/slots/?limit=50
    """
    _build_search_index()
    limit = int(request.GET.get('limit', 50))
    slots = search_engine.get_slot_extraction_sample(limit=limit)
    return JsonResponse({'slots': slots})
