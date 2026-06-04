"""
MEDAI Qidiruv Tizimi (Information Retrieval Engine)
=====================================================
Ushbu modul quyidagi funksiyalarni o'z ichiga oladi:
1. Tokenizatsiya - matnni so'zlarga ajratish
2. Teskari indeks (Inverted Index) - tokenlardan hujjatlar ro'yxatini yaratish
3. TF-IDF modeli - term frequency-inverse document frequency
4. BM25 modeli - Best Match 25 (zamonaviy qidiruv algoritmi)
"""

import math
import re
from collections import defaultdict


# ===========================================================
# 1. TOKENIZATSIYA - matnni so'zlarga ajratish
# ===========================================================

STOP_WORDS = {
    'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
    'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
    'could', 'should', 'may', 'might', 'shall', 'can', 'that', 'this',
    'these', 'those', 'it', 'its', 'as', 'if', 'not', 'no', 'so',
}


def tokenize(text: str) -> list[str]:
    """
    Matnni tokenlarga (so'zlarga) ajratadi.
    
    Jarayon:
    1. Kichik harflarga o'tkazish
    2. Faqat harf va raqamlarni qoldirish
    3. So'zlarga bo'lish
    4. Stop-words (keraksiz so'zlar)ni olib tashlash
    5. Juda qisqa tokenlarni olib tashlash
    
    Misol:
        tokenize("Python dasturlash tili") 
        => ['python', 'dasturlash', 'tili']
    """
    if not text:
        return []
    
    # Kichik harflarga o'tkazish
    text = text.lower()
    
    # Faqat harf va raqamlarni qoldirish (tinish belgilarini olib tashlash)
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    
    # So'zlarga bo'lish
    tokens = text.split()
    
    # Stop-words va juda qisqa tokenlarni olib tashlash
    tokens = [t for t in tokens if t not in STOP_WORDS and len(t) > 1]
    
    return tokens


def tokenize_with_positions(text: str) -> dict:
    """
    Tokenlarni pozitsiyalari bilan qaytaradi.
    
    Qaytaradi:
        {'python': [0, 5], 'dasturlash': [1], 'tili': [2]}
        (har bir token qaysi pozitsiyalarda uchrashini ko'rsatadi)
    """
    tokens = tokenize(text)
    positions = defaultdict(list)
    
    for pos, token in enumerate(tokens):
        positions[token].append(pos)
    
    return dict(positions)


# ===========================================================
# 2. TESKARI INDEKS (Inverted Index)
# ===========================================================

class InvertedIndex:
    """
    Teskari indeks: har bir token uchun uni o'z ichiga olgan
    hujjatlar ro'yxatini saqlaydi.
    
    Tuzilish:
        {
            'python': {1: [0, 5], 2: [3]},     # 1-hujjatda 0 va 5-pozitsiyada, 2-hujjatda 3-pozitsiyada
            'dasturlash': {1: [1], 3: [0]},     # 1-hujjatda 1-pozitsiyada, 3-hujjatda 0-pozitsiyada
        }
    """
    
    def __init__(self):
        # token -> {doc_id: [pozitsiyalar]}
        self.index = defaultdict(lambda: defaultdict(list))
        # doc_id -> hujjat uzunligi (tokenlar soni)
        self.doc_lengths = {}
        # doc_id -> asl matn
        self.documents = {}
        # Jami hujjatlar soni
        self.total_docs = 0
    
    def add_document(self, doc_id: int, text: str):
        """
        Yangi hujjatni indeksga qo'shadi.
        
        Parametrlar:
            doc_id: Hujjat identifikatori (masalan, Article ID)
            text: Hujjat matni
        """
        positions = tokenize_with_positions(text)
        tokens = tokenize(text)
        
        self.documents[doc_id] = text
        self.doc_lengths[doc_id] = len(tokens)
        self.total_docs += 1
        
        # Har bir token uchun indeksni yangilash
        for token, pos_list in positions.items():
            self.index[token][doc_id] = pos_list
    
    def search(self, token: str) -> dict:
        """
        Berilgan token qaysi hujjatlarda borligini qaytaradi.
        
        Qaytaradi:
            {doc_id: [pozitsiyalar]} yoki {} (topilmasa)
        """
        return dict(self.index.get(token, {}))
    
    def search_multi(self, tokens: list[str]) -> set:
        """
        Bir nechta tokenning barchasi mavjud hujjatlarni qaytaradi (AND operatsiyasi).
        """
        if not tokens:
            return set()
        
        result_sets = [set(self.index[t].keys()) for t in tokens if t in self.index]
        
        if not result_sets:
            return set()
        
        # Barcha tokenlarda mavjud hujjatlar (kesishma)
        return set.intersection(*result_sets)
    
    def get_stats(self) -> dict:
        """Indeks statistikasini qaytaradi."""
        return {
            'total_docs': self.total_docs,
            'unique_tokens': len(self.index),
            'avg_doc_length': sum(self.doc_lengths.values()) / max(self.total_docs, 1),
        }


# ===========================================================
# 3. TF-IDF MODELI
# ===========================================================

class TFIDFSearchEngine:
    """
    TF-IDF (Term Frequency - Inverse Document Frequency) qidiruv tizimi.
    
    TF (Term Frequency) = so'z hujjatda necha marta uchraydi / hujjat uzunligi
    IDF (Inverse Document Frequency) = log(jami hujjatlar / so'z bor hujjatlar)
    TF-IDF = TF * IDF
    
    Yuqori TF-IDF: so'z bu hujjatda ko'p, boshqalarida kam => muhim so'z
    """
    
    def __init__(self):
        self.inverted_index = InvertedIndex()
    
    def add_document(self, doc_id: int, text: str):
        """Hujjatni qidiruv tizimiga qo'shadi."""
        self.inverted_index.add_document(doc_id, text)
    
    def tf(self, token: str, doc_id: int) -> float:
        """
        Term Frequency hisoblash.
        TF = (tokenning hujjatdagi soni) / (hujjat uzunligi)
        """
        positions = self.inverted_index.index.get(token, {}).get(doc_id, [])
        doc_length = self.inverted_index.doc_lengths.get(doc_id, 1)
        
        if doc_length == 0:
            return 0.0
        
        return len(positions) / doc_length
    
    def idf(self, token: str) -> float:
        """
        Inverse Document Frequency hisoblash.
        IDF = log(N / df) 
        N = jami hujjatlar, df = so'z bor hujjatlar soni
        """
        total_docs = self.inverted_index.total_docs
        doc_freq = len(self.inverted_index.index.get(token, {}))
        
        if doc_freq == 0:
            return 0.0
        
        return math.log(total_docs / doc_freq)
    
    def tfidf_score(self, token: str, doc_id: int) -> float:
        """TF-IDF ballini hisoblash."""
        return self.tf(token, doc_id) * self.idf(token)
    
    def search(self, query: str, top_k: int = 10) -> list[dict]:
        """
        TF-IDF asosida qidiruv o'tkazadi.
        
        Parametrlar:
            query: Qidiruv so'rovi matni
            top_k: Qaytariladigan natijalar soni
        
        Qaytaradi:
            [{'doc_id': ..., 'score': ..., 'text': ...}, ...]
        """
        query_tokens = tokenize(query)
        
        if not query_tokens:
            return []
        
        # Potensial hujjatlarni topish
        candidate_docs = set()
        for token in query_tokens:
            candidate_docs.update(self.inverted_index.index.get(token, {}).keys())
        
        # Har bir hujjat uchun umumiy TF-IDF ball hisoblash
        scores = {}
        for doc_id in candidate_docs:
            score = sum(self.tfidf_score(token, doc_id) for token in query_tokens)
            scores[doc_id] = score
        
        # Ball bo'yicha saralash
        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        return [
            {
                'doc_id': doc_id,
                'score': round(score, 4),
                'text': self.inverted_index.documents.get(doc_id, ''),
                'model': 'TF-IDF',
            }
            for doc_id, score in sorted_results[:top_k]
            if score > 0
        ]


# ===========================================================
# 4. BM25 MODELI
# ===========================================================

class BM25SearchEngine:
    """
    BM25 (Best Match 25) qidiruv tizimi.
    
    BM25 - TF-IDFning yaxshilangan versiyasi. U ikkita muhim muammoni hal qiladi:
    1. TF normalizatsiyasi - so'z ko'p takrorlansa ham ball oshib ketmaydi
    2. Hujjat uzunligi normalizatsiyasi - uzun hujjatlar adolatli baholanadi
    
    Formula:
    BM25(q,d) = Σ IDF(qi) * [TF(qi,d) * (k1+1)] / [TF(qi,d) + k1*(1-b+b*|d|/avgdl)]
    
    k1 = 1.5 (TF to'yinish parametri, odatda 1.2-2.0)
    b = 0.75 (uzunlik normalizatsiya parametri, 0=yo'q, 1=to'liq)
    """
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.inverted_index = InvertedIndex()
    
    def add_document(self, doc_id: int, text: str):
        """Hujjatni qidiruv tizimiga qo'shadi."""
        self.inverted_index.add_document(doc_id, text)
    
    def _avg_doc_length(self) -> float:
        """O'rtacha hujjat uzunligini hisoblaydi."""
        lengths = self.inverted_index.doc_lengths
        if not lengths:
            return 1.0
        return sum(lengths.values()) / len(lengths)
    
    def idf(self, token: str) -> float:
        """
        BM25 uchun IDF hisoblash (Robertson-Jones varianti).
        IDF = log((N - df + 0.5) / (df + 0.5) + 1)
        """
        N = self.inverted_index.total_docs
        df = len(self.inverted_index.index.get(token, {}))
        
        return math.log((N - df + 0.5) / (df + 0.5) + 1)
    
    def bm25_score(self, token: str, doc_id: int) -> float:
        """
        Bitta token uchun BM25 ballini hisoblaydi.
        """
        positions = self.inverted_index.index.get(token, {}).get(doc_id, [])
        tf = len(positions)  # tokenning hujjatdagi soni
        doc_length = self.inverted_index.doc_lengths.get(doc_id, 1)
        avgdl = self._avg_doc_length()
        
        # BM25 formulasi
        numerator = tf * (self.k1 + 1)
        denominator = tf + self.k1 * (1 - self.b + self.b * doc_length / avgdl)
        
        return self.idf(token) * (numerator / denominator)
    
    def search(self, query: str, top_k: int = 10) -> list[dict]:
        """
        BM25 asosida qidiruv o'tkazadi.
        
        Parametrlar:
            query: Qidiruv so'rovi matni
            top_k: Qaytariladigan natijalar soni
        
        Qaytaradi:
            [{'doc_id': ..., 'score': ..., 'text': ...}, ...]
        """
        query_tokens = tokenize(query)
        
        if not query_tokens:
            return []
        
        # Potensial hujjatlarni topish
        candidate_docs = set()
        for token in query_tokens:
            candidate_docs.update(self.inverted_index.index.get(token, {}).keys())
        
        # Har bir hujjat uchun umumiy BM25 ball hisoblash
        scores = {}
        for doc_id in candidate_docs:
            score = sum(self.bm25_score(token, doc_id) for token in query_tokens)
            scores[doc_id] = score
        
        # Ball bo'yicha saralash
        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        return [
            {
                'doc_id': doc_id,
                'score': round(score, 4),
                'text': self.inverted_index.documents.get(doc_id, ''),
                'model': 'BM25',
            }
            for doc_id, score in sorted_results[:top_k]
            if score > 0
        ]


# ===========================================================
# 5. YAGONA INTERFEYS - TF-IDF va BM25 ni birlashtirish
# ===========================================================

class MEDAISearchEngine:
    """
    MEDAI loyihasi uchun asosiy qidiruv tizimi.
    TF-IDF va BM25 modellarini bir joyda taqdim etadi.
    """
    
    def __init__(self):
        self.tfidf = TFIDFSearchEngine()
        self.bm25 = BM25SearchEngine()
        self._is_built = False
    
    def index_document(self, doc_id: int, text: str):
        """Hujjatni ikkala modelga ham indekslaydi."""
        self.tfidf.add_document(doc_id, text)
        self.bm25.add_document(doc_id, text)
    
    def index_from_queryset(self, queryset, text_field: str = 'name', id_field: str = 'id'):
        """
        Django queryset dan hujjatlarni indekslaydi.
        
        Misol:
            engine.index_from_queryset(Article.objects.all(), text_field='content')
        """
        for obj in queryset:
            doc_id = getattr(obj, id_field)
            text = getattr(obj, text_field, '') or ''
            self.index_document(doc_id, text)
        self._is_built = True
    
    def search(self, query: str, model: str = 'bm25', top_k: int = 10) -> dict:
        """
        Qidiruv o'tkazadi.
        
        Parametrlar:
            query: Qidiruv so'rovi
            model: 'bm25' yoki 'tfidf'
            top_k: Natijalar soni
        
        Qaytaradi:
            {
                'query': ...,
                'tokens': [...],
                'model': ...,
                'results': [...],
                'total': ...,
            }
        """
        query_tokens = tokenize(query)
        
        if model == 'tfidf':
            results = self.tfidf.search(query, top_k)
        else:
            results = self.bm25.search(query, top_k)
        
        return {
            'query': query,
            'tokens': query_tokens,
            'model': model.upper(),
            'results': results,
            'total': len(results),
        }
    
    def compare_models(self, query: str, top_k: int = 5) -> dict:
        """
        TF-IDF va BM25 natijalarini solishtiradi.
        """
        return {
            'query': query,
            'tokens': tokenize(query),
            'tfidf_results': self.tfidf.search(query, top_k),
            'bm25_results': self.bm25.search(query, top_k),
        }
    
    def get_index_stats(self) -> dict:
        """Indeks statistikasini qaytaradi."""
        return {
            'tfidf': self.tfidf.inverted_index.get_stats(),
            'bm25': self.bm25.inverted_index.get_stats(),
        }

    def get_token_frequencies(self, limit: int = 100) -> list[dict]:
        """Barcha tokenlar va ularning chastotalarini qaytaradi."""
        index = self.bm25.inverted_index.index
        freqs = []
        for token, docs in index.items():
            count = sum(len(pos) for pos in docs.values())
            freqs.append({
                'token': token,
                'count': count,
                'doc_count': len(docs)
            })
        
        # Eng ko'p uchraydiganlarni saralash
        freqs.sort(key=lambda x: x['count'], reverse=True)
        return freqs[:limit]

    def get_inverted_index_sample(self, limit: int = 50) -> dict:
        """Teskari indeksdan namuna qaytaradi."""
        index = self.bm25.inverted_index.index
        sample = {}
        for i, (token, docs) in enumerate(index.items()):
            if i >= limit:
                break
            # Faqat doc_id larni qaytarish
            sample[token] = list(docs.keys())[:10]  # Har bir token uchun max 10 ta doc
        return sample

    def get_slot_extraction_sample(self, limit: int = 50) -> list[dict]:
        """50 ta gapni slotlarga ajratib qaytaradi."""
        docs = list(self.bm25.inverted_index.documents.items())[:limit]
        results = []
        for doc_id, text in docs:
            words = text.split()
            if len(words) >= 3:
                results.append({
                    'id': doc_id,
                    'text': text,
                    'slots': {
                        'subject': words[0],
                        'predicate': words[1],
                        'object': " ".join(words[2:])
                    }
                })
            else:
                results.append({
                    'id': doc_id,
                    'text': text,
                    'slots': {'subject': text, 'predicate': '', 'object': ''}
                })
        return results


# ===========================================================
# Global instance - ilovada bir marta yaratiladi
# ===========================================================
search_engine = MEDAISearchEngine()

# ===========================================================
# 6. XLSX DATASET LOADER
# ===========================================================
import os

def load_xlsx_to_engine(engine: MEDAISearchEngine, filepath: str) -> dict:
    """
    .xlsx fayldan ma'lumotlarni o'qib, qidiruv indeksiga yuklaydi.

    Kutilayotgan ustunlar: ID, Name, Description
    Qidiruv: Description ustuni bo'yicha ishlaydi.

    Parametrlar:
        engine   : MEDAISearchEngine instance
        filepath : xlsx fayl yo'li (masalan: 'data/dataset.xlsx')

    Qaytaradi:
        {'loaded': 150, 'skipped': 3, 'errors': [...]}
    """
    try:
        from openpyxl import load_workbook
    except ImportError:
        return {'error': "openpyxl o'rnatilmagan. 'pip install openpyxl' bajaring."}

    if not os.path.exists(filepath):
        return {'error': f"Fayl topilmadi: {filepath}"}

    wb = load_workbook(filepath, read_only=True)
    ws = wb.active

    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return {'error': "Fayl bo'sh"}

    # Birinchi qator — ustun nomlari
    headers = [str(h).strip().lower() if h else '' for h in rows[0]]

    # Ustun indekslarini aniqlash
    try:
        id_col   = headers.index('id')
    except ValueError:
        id_col   = 0  # topilmasa birinchi ustun

    try:
        # data.xlsx da 'matn' ustuni bor
        desc_col = headers.index('matn')
    except ValueError:
        try:
            desc_col = headers.index('description')
        except ValueError:
            desc_col = 1

    try:
        # data.xlsx da 'label' ustuni bor
        label_col = headers.index('label')
    except ValueError:
        try:
            label_col = headers.index('name')
        except ValueError:
            label_col = 2

    loaded  = 0
    skipped = 0
    errors  = []

    for i, row in enumerate(rows[1:], start=2):  # 1-qator header
        try:
            doc_id = row[id_col] if row[id_col] is not None else i
            text   = str(row[desc_col] or '').strip()
            label  = str(row[label_col] or '').strip()

            if not text:          # Matn bo'sh bo'lsa o'tkazib yuborish
                skipped += 1
                continue

            # Qidiruv matni: Matn + Label (ikkalasini birlashtiramiz)
            search_text = f"{text} {label}".strip()

            engine.index_document(int(doc_id), search_text)
            loaded += 1

        except Exception as e:
            errors.append(f"Qator {i}: {e}")

    wb.close()
    engine._is_built = True

    return {
        'loaded' : loaded,
        'skipped': skipped,
        'errors' : errors,
        'file'   : os.path.basename(filepath),
    }