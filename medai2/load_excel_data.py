"""
data.xlsx datasetini qidiruv indeksiga yuklash skripti
"""
import pandas as pd
import json
import sys
import os
import re
from collections import defaultdict

# Django sozlamalarini yuklab olish (manage.py bilan bir papkada ishlaydi)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# Django environment sozlash
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medai.settings')

try:
    import django
    django.setup()
    from dashboard.search_engine import InvertedIndex, BM25
except Exception:
    # Agar Django yuklanmasa, to'g'ridan-to'g'ri import qilish
    sys.path.insert(0, os.path.join(BASE_DIR, 'dashboard'))
    from search_engine import InvertedIndex, BM25

STOP_WORDS = {
    'va', 'yoki', 'lekin', 'ammo', 'bilan', 'uchun', 'bu', 'shu',
    'ular', 'biz', 'men', 'sen', 'ham', 'esa', 'da', 'ga', 'ni',
    'ning', 'dan', 'bir', 'deb', 'ki', 'agar', 'har', 'oz', 'bor',
    'yoq', 'emas', 'uni', 'uning', 'bizning', 'ko', 'bo', 'qil',
    'keyin', 'oldin', 'hatto', 'faqat', 'chunki', 'agar', 'bunda',
    'ва', 'ёки', 'лекин', 'аммо', 'билан', 'учун', 'бу', 'шу',
    'улар', 'биз', 'мен', 'сен', 'ҳам', 'эса', 'да', 'га', 'ни',
    'нинг', 'дан', 'бир', 'деб', 'ки', 'агар', 'ҳар', 'оз', 'бор',
    'йўқ', 'эмас', 'уни', 'унинг', 'бизнинг', 'кейин', 'олдин',
    'ҳатто', 'фақат', 'чунки', 'бунда', 'эди', 'бўлди', 'бўлган',
}

def tokenize_universal(text: str) -> list:
    if not text or str(text).strip() == '' or str(text) == 'nan':
        return []
    text = str(text).lower()
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    tokens = text.split()
    tokens = [t for t in tokens if len(t) >= 2 and t not in STOP_WORDS and not t.isdigit()]
    return tokens

class UniversalInvertedIndex(InvertedIndex):
    def add_document(self, doc_id: str, text: str) -> None:
        tokens = tokenize_universal(text)
        self.doc_lengths[str(doc_id)] = len(tokens)
        self.total_docs += 1
        for position, token in enumerate(tokens):
            self.index[token][str(doc_id)].append(position)

def load_excel_dataset(excel_path: str):
    print(f"Dataset o'qilmoqda: {excel_path}")
    df = pd.read_excel(excel_path)
    print(f"Jami qatorlar: {len(df)}")

    df["Matn"] = df["Matn"].astype(str).str.strip()
    df = df[df["Matn"] != ""]
    df = df[df["Matn"] != "nan"]

    index = UniversalInvertedIndex(use_medical_tokenizer=False)
    print("\nIndekslash boshlandi...")

    for i, row in df.iterrows():
        try:
            doc_id = str(row["ID"])
            text = str(row["Matn"])
            label = str(row.get("Label", ""))
            full_text = f"{text} {label}"
            index.add_document(doc_id, full_text)
        except Exception:
            pass

    print(f"\nIndekslandi: {index.total_docs} hujjat")
    print(f"Unikal tokenlar: {len(index.index)}")

    output_path = os.path.join(BASE_DIR, "search_index.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(index.to_dict(), f, ensure_ascii=False)
    print(f"\nIndeks '{output_path}' ga saqlandi!")

if __name__ == "__main__":
    # Excel fayl yo'li — loyiha papkasidagi data/ ichida
    excel_file = os.path.join(BASE_DIR, "data", "data.xlsx")
    if not os.path.exists(excel_file):
        print(f"XATO: Fayl topilmadi: {excel_file}")
        sys.exit(1)
    load_excel_dataset(excel_file)
