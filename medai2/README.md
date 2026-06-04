# MEDAI Dashboard

Django-based medical AI dashboard with search engine.

## Local ishga tushirish

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Render.com deploy qilish

1. GitHub-ga yuklang:
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/USERNAME/medai.git
git push origin main
```

2. render.com → New → Web Service → GitHub reponi tanlang
3. Sozlamalar:
   - **Build Command:** `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
   - **Start Command:** `gunicorn medai.wsgi --log-file -`
4. Environment Variables (ixtiyoriy):
   - `SECRET_KEY` = (xavfsiz kalit)
   - `DEBUG` = `False`

## Loyiha tuzilmasi

```
medai2/
├── dashboard/          # Asosiy app
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── search_engine.py
│   ├── static/
│   └── templates/
├── medai/              # Sozlamalar
│   ├── settings.py
│   └── urls.py
├── data/               # data.xlsx
├── requirements.txt    # Kutubxonalar
├── Procfile            # Render/Heroku uchun
└── manage.py
```
