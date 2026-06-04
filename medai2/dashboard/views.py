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
    """Real dataset namunalari bilan indeks yaratadi (216 ta hujjat)."""
    if search_engine._is_built:
        return
    demo_docs = [
        (1, "Ularning nomlanishidan ma’lumki, ular endokrin tizimiga taalluqli bo‘lmagan turli to‘qimalarda sintezlanadi. Endokrinotsitlarda sintezlanuvchi gormonl Endocr"),
        (2, "Sekretsiyadan keyin ko‘pgina suvda eruvchan gormonlar (oqsil, peptid, adrenalin) eritma ko‘rinishida plazmada aylanadi. Gidrofob gormonlar tashuvchanl Endocr"),
        (3, "Ko‘pgina hujayraviy membrananing oqsil va peptid guruhlari gormonlari uchun o‘zidan o‘tkazmaslik xos, shuning uchun ularning ta’siri hujayra membranas Endocr"),
        (4, "Jarayon siklli adenozinmonofosfat, siklli guanozinmonofosfat, ionlashgan kalsiy, fosfatidilinozitlarning 'ikkinchi messendjer'i hosil bo‘lishi bilan b Endocr"),
        (5, "Organizm darajasiga gormonlarning hamma asosiy vazifalarining liar xilligini to‘rtta asosiy: bo‘y, organizm rivojlanishi, reproduksiya, gomeostazni qo Endocr"),
        (6, "Natijada tizim dinamik tenglashadi, bu moslashish jarayonida o‘zgarishi yoki patologik holatlarda buzilishi mumkin. Endokrin tizim hosil bo‘lishida or Endocr"),
        (7, "еибои - ichkariga, кршо - ajrataman, .ijrataman va Aoyoq - so‘z, ta’limot) ichki sekretsiya bezlarining luzilishi va rivojlanishi, bu bezlar ishlab ch Endocr"),
        (8, "Bu endokrinologiya sohasidagi ilk tajriba edi (1849).Dastlab ichki sekretsiya bezlari degan tushuncha nemis fiziologi va tabiat tadqiqotchisi D.Myulle Endocr"),
        (9, "Bazedov (1840) diffuz toksik buqoqni, ingliz vrachi T.Adisson (1855) surunkali buyrak usti bezi yetishmovchiligi klinikasini izohlashdi. Shvetsariyali Endocr"),
        (10, "XX asrning boshlariga kelib, endokrinologiya fan sifatida rivojlandi. Ko‘pgina gormonlar: adrenalin (1901), tiroksin (1915), progesteron, testosteron  Endocr"),
        (11, "X.To‘raqulov, Sh.Sh.Ilyosov, V.N.Fedoseev, T.M.Muhamedov va boshqalar). Bu kasallikning oldini olish uchun 1954-yil Toshkentda bo‘qoqqa qarshi dispans Endocr"),
        (12, "R.Q.Islombekov, Y.X.To‘raqulov dunyoda birinchi bo‘lib buqoq kasalligini aniqlash va davolashning yangi usulini ishlab chiqib, nufuzli mukofotga sazov Endocr"),
        (1234, "Ginekologiya-ayol organizmi uchun xos anatomik va fiziologik xususiyatlarini, jinsiy a’zolarining kasalliklarini, ularni davolash hamda oldini olish y OB/GYN"),
        (1235, "Ginekologiya tibbiyotning ko’pgina boshqa sohalari – anatomiya, gistologiya, patologik va topografik anatomiya, patologik fiziologiya, immunologiya, m OB/GYN"),
        (1236, "Ayollar kasalliklari to’g’risida qisqacha ma’lumotlarni Hindiston, Misr va Yunoniston qo’lyozmalarida uchratish mumkin. Тibbiyot ilmining bobokaloni b OB/GYN"),
        (1237, "Ginekologiya fanining taraqqiyotiga katta hissa qo’shgan olimlardan biri Тoshkent meditsina instituti akusherlik va ginekologiya kafedrasining mudiri  OB/GYN"),
        (1238, "Bundan tashqari, olim tomonidan homiladorlikdan muhofaza qilishning yangi operativ usuli ham yaratildi. O’zbekistonda tibbiyot fanining rivojlanishiga OB/GYN"),
        (1239, "Bu kitob 1960 yili Sog’liqni saqlash Vazirligining davlat meditsina nashriyoti tomonidan chiqarildi. Akusherlik va ginekologiya ixtisosligi bo’yicha m OB/GYN"),
        (1240, "Ular tomonidan bo’qoq bezi kasalliklarining jinsiy a’zolar faoliyatiga ta’siri o’rganilmoqda. Shu kasallikka chalingan ayollarda homiladorlikdan saqla OB/GYN"),
        (1241, "5 AYOLLAR JINSIY A’ZOLARINING ANAТOMIYASI Maqsad. Ayollarning tashqi va ichki jinsiy a’zolari anatomiyasini bilish. Jinsiy a’zolarning qon, limfa tomi OB/GYN"),
        (1242, "Тashqi jinsiy a’zolarga qov, katta va kichik jinsiy lablar, klitor, qin dahlizi, qizlik pardasi kirsa, ichki jinsiy a’zolarga qin, bachadon, bachadon  OB/GYN"),
        (1243, "Katta jinsiy lablar jinsiy yoriq bilan bir-biridan ajralib turadi. Ayol tashqi jinsiy a’zolarining tuzilishi. Bu bezlarning chiqarish yo’llari kichik  OB/GYN"),
        (1244, "Normada jinsiy yoriq yumilib turadi va qinga infeksiya o’tishi va qurib qolishdan saqlaydi. Klitor jinsiy yoriqning oldingi burchagida joylashgan, qon OB/GYN"),
        (1245, "Qizlik pardasi tashqi va ichki jinsiy organlarni bir-biridan ajratib turadigan biriktiruvchi to’qimadan iborat yupqa to’siqdir. Bu parda halqasimon, y OB/GYN"),
        (8120, "Yallig‘lanishga stafilokokklar, kam hollarda boshqa mikroblar sabab bo‘ladi. Mikrob va ularning toksinlari patogenetik ahamiyatga ega. Limfangit kam h Infect"),
        (8121, "Morfologik o‘zgarishlarga to‘qimalar shishi, mayda limfa tomirlari atrofida tarqaluvchi infiltrat avj olishi xosdir. To‘qimalar infiltratsiyasi, mikro Infect"),
        (8122, "Ba’zida fil oyog‘i kasalligi kuzatilishi mumkin (elephantiasis). Klinik manzarasi jarayonning oldini olishga, infeksiyaning virulentligiga, mahalliy t Infect"),
        (8123, "Yirikroq limfa tomirlarida (lymphangitis truncularis) ingichka qizil yo‘llar bo‘ladi. Ular o‘choqdan regional limfa tugunlariga cho‘zilib boradi. Shis Infect"),
        (8124, "To‘qima flegmonalari, saramas, abssesslar, ko‘chib yuruvchi tromboflebit va sepsis ro‘y berganda ikkilamchi asoratlar rivojlanadi. Differensial diagno Infect"),
        (8125, "Isituvchi kompresslar va boshqa fizioterapevtik tadbirlar bajariladi. Antibiotiklar va sulfanilamidlar tavsiya qilinadi. Oqma yara, flegmona, abssess  Infect"),
        (8126, "Surunkali bosqichda balneologik davo va kam dozalarda rentgenoterapiya qo‘llaniladi. LIMFA TUGUNLARINING YaLLIG‘LANIShI (LIMFADENIT) Qo‘zg‘atuvchilari Infect"),
        (8127, "Gematogen yo‘l bilan tarqalishi kam uchraydi. Ayrim hollarda infeksiyaning kontakt orqali tarqalishi kuzatiladi. 94-rasm. Jag‘ osti limfadeniti Yallig Infect"),
        (8128, "Periadenit rivojlanadi. Zardobli yallig‘lanish fazasida shish, limfa tuguni gepermiyasi bo‘ladi. So‘ng fibrinoz ekssudatsiya bo‘ladi, yiringli shish k Infect"),
        (8129, "Yiring yorilgan hollarda uzoq bitmaydigan oqmalar kuzatiladi. O‘tkir limfaplaziya, fibroz induratsiya vujudga keladi. Klinik manzarasi. Tugunda og‘riq Infect"),
        (8130, "Dastlabki bosqichda tugunlarni paypaslab ko‘rish mumkin, keyinchalik ular qo‘shilib, yagona konglomerat hosil qilishadi. Virulentlik kuchsizroq bo‘lsa Infect"),
        (8131, "Leykotsitoz, leykotsitar formulada chapga siljish aniqlanadi. Differensial diagnozi. Limfadenitni ter bezlari yallig‘lanishida, abssess yoki flegmonad Infect"),
        (8558, "Jigar kasalligi. Buyrak kasalligi yoki nefrotik sindrom (albumin darajasi past boʻlgan buyrak kasalligi. Albumin qondagi muhim oqsildir); Surunkali ve Cardio"),
        (8559, "2-usul Ratsion va turmush tarzini oʻzgartiring Tuzni iste’mol qilishni kamaytiring. Qondagi ortiqcha tuz toʻqimalarda suvni saqlaydi. Shuning uchun, t Cardio"),
        (8560, "Biroq, bir nechta 233 umumiy maslahatlar bilan siz tuz iste’molini ham kamaytirishingiz mumkin. Ovqatni tuz bilan ta’tib koʻrmang. Kamroq tuzli ta’mga Cardio"),
        (8561, "Qayta ishlangan ovqatlarni iste’mol qilishni cheklang. Bunga supermarketda xarid qilishingiz mumkin boʻlgan barcha konservalangan, mo’z latilgan yoki  Cardio"),
        (8562, "Yaxshi yondashuv supermarketlarda xarid qilish va markazdagi 'savdo orollari' dan qochishdir. Goʻsht, baliq, sut mahsulotlari va qadoqlangan oziq-ovqa Cardio"),
        (8563, "Qayta ishlangan ovqatlardagi yorliqni oʻqing va natriy tarkibini tekshiring. Sizning dietangizdagi ozuqaviy muvozanatni yaxshilang. Turli xil meva va  Cardio"),
        (8564, "Qushqoʻnmas, maydanoz, lavlagi, uzum, yashil loviya, yashil bargli sabzavotlar, qovoq, ananas, piyoz, piyoz va sarimsoq kabi turli xil meva va sabzavo Cardio"),
        (8565, "Siz goʻsht iste’molini cheklashingiz kerak. Goʻshtning ba’zi turlari (masalan, dudlangan goʻsht, sovuq goʻsht va qizil goʻsht) natriyning yuqori qismi Cardio"),
        (8566, "Agar siz suv saqlasangiz, koʻproq suv ichish mantiqsiz boʻlib tuyulishi mumkin. Biroq, bu tizimni tozalashning eng yaxshi usuli. Kuniga oltisakkiz sta Cardio"),
        (8567, "Spirtli ichimliklar, kofein va tamakidan saqlaning. Ushbu mahsulotlar ichki shishishni kuchaytirishi va umumiy sogʻligʻingizni yomonlashtirishi mumkin Cardio"),
        (8568, "235 Toʻgʻri va yetarli darajada mashq qiling. Ma’lumki, agar siz yetarli darajada harakat qilmasangiz, shish paydo boʻlishi mumkin. Koʻp odamlar shish Cardio"),
        (8569, "Agar siz izchil mashgʻulotlarga oʻrganmagan boʻlsangiz, asta-sekin mashq qilishni boshlang. Agar siz jarrohlik yoki kasallikdan tuzalib ketgan boʻlsan Cardio"),
        (9196, "Oliy nerv faoliyati va markaziy nerv sistemasi fiziologiyasi fani tibbiyot yo’nalishidagi odam anatomiyasi, fiziologiyasi va umumiy gigiyenasi fanlari Psych"),
        (9197, "Oliy nerv faoliyati va markaziy nerv sistemasi fiziologiyasi fanining boshqa fanlar bilan aloqasi. Oliy nerv faoliyati va markaziy nerv sistemasi fizi Psych"),
        (9198, "Katta yarim sharlar fiinksiyalarini nihoyatda xilma-xil usullar yordamida o’rgansa boʻladi. Stiulardan ba’zilarini aytib oʻtamiz: Kuzatish usuli-hayvo Psych"),
        (9199, "Shu sababli u boshqa usullar bilan birga qullaniladi. Miya poʻstlogʻini ta’sirlash usuli - katta yarim sharlarining u yoki bu qismlari ta’sirlanganda  Psych"),
        (9200, "Natijada organizmga ro’y bergan oʻzgarishlarga qarab, shu hayvon miyasi poʻstlogʻi yoki ma’lum qismlarining organizm uchun ahamiyati o’rganiladi. Oliy Psych"),
        (9201, "Olimning tabobat sohasida qilgan ishlari o’sha davr tabobatini bir necha asrlarga ilgarilatdi va ayrim sohalarda hatto hozirgi zamon tibbiyotiga yaqin Psych"),
        (9202, "P. Pavlovlaming roli benihoya katta boʻldi. Bosh miya faoliyatining reflektor xarakterga ega ekanligini dastlab, I. M. Seche-nov oʻzining mashhur 'Bos Psych"),
        (9203, "Seche-nov oʻzining mashhur 'Bosh miya reflekslari' asarida ta’riflab berdi va shu bilan oliy nerv faoliyati haqidagi ta’limotga zamin yaratdi. Keyinch Psych"),
        (9204, "I. P. Pav-lov poʻstloq faoliyatini atroflicha oʻrganib, oliy nerv faoliyati haqida materialistik ta’limot yaratdi. I. P. Psych"),
        (9205, "P. Pavlov asoslagan shartli reflekslar usuli katta yarim sharlar poʻstlogʻining faoliyatini oʻrganishda muhim ahamiyatga ega boʻldi. Faqat ana shu usu Psych"),
        (9206, "MAT - bosh va orqa miyadan iborat bo‘lib, o‘zaro bogiangan neyronlaming majmuasi hisoblanadi. Bosh miya va orqa miyani ko’ndalang kesimi ko’rilganda h Psych"),
        (9207, "Asab tizimining bir qancha vazifalari bo’lib, ular quidagilardan iborat: s integrativ funksiya - axborotni tezlik bilan aniq uzatish va uni integratsi Psych"),
        (10629, "Pediatriya fani talabalarda turli yoshdagi sog‘lom va bemor bolalar tanaini anatomo-fiziologik hususiyatlari, jismoniy rivojlanishini monitoring qilis Ped"),
        (10630, "Tibbiyot oliy ta’lim muassasasi Biotibbiyot muxandisligi yo‘nalishining uchinchi bosqichida pediatriya fani o‘rganiladi. Bu, aslida, kelajakdagi Bioti Ped"),
        (10631, "Pediatriyaning rivojlanish tarixi. Bolalik davrlari. Jismoniy rivojlanish monitoringi. Pediatriya faniga kirish. Pediatriyaning rivojlanish tarixi. Ped"),
        (10632, "Pediatriyaning rivojlanish tarixi. O‘zbekistonda pediatriyani rivojlanishi Bolalik davrlari. Bolalarni shifoxona sharoitida ovqatlantirishni tashkil q Ped"),
        (10633, "Ko‘krak sutining ahamiyati. Qo‘shimcha ovqat berish tamoyillari. Onalarga bolalarni ovqatlantirish bo‘yicha tavsiyalar Oqsil-energetik yetishmovchilik Ped"),
        (10634, "Suyak tizimining asosiy kasalliklari semiotikasi. Bolalarda raxit kasalligi. Bolalarda mushak tizimini anatomo-fiziologik xususiyatlari. Mushaklar tiz Ped"),
        (10635, "Mushak tizimining asosiy kasalliklari semiotikasi. 4-bob. Bolalarda qon va qon hosil bo‘lish a’zolari anatomik fiziologik hususiyatlari. Bronxitlar. P Ped"),
        (10636, "Pnevmoniyalar. Bolalar nafas tizimini yoshiga ko‘ra anatomik-fiziologik hususiyatlari. Tashqi nafas faoliyatlarini baholash usullari va mezonlari. Naf Ped"),
        (10637, "Bolalarda yurak qon-tomir tizimining anatomo-fiziologik hususiyatlari. Bolalarda uchraydigan yurak qon-tomir tizimi kasalliklari semiotikasi. Bolalard Ped"),
        (10638, "Shuning uchun insonning bolalik davri qanday kechganligi, qanday muhitda va sharoitda tarbiya topib, o‘sganligi uning kelajakdagi salomatlik darajasin Ped"),
        (10639, "Pediatr bola va uning ota-onasi bilan doimiy muloqotda bo‘ladi. Bolalar shifokori yaxshi ruhshunos va pedagog bo‘lishi zarur. Bu uning bemor va uning  Ped"),
        (10640, "Bola injiq, yig‘loqi bo‘lib qoladi. Bunday holatda bolani ko‘rikdan o‘tkazish qiyin kechadi. Ammo shifokor uni sinchkovlik bilan tekshirishi va to‘g‘r Ped"),
        (13385, "Xirurgiya rivojlаnish tаrixi Tarixiy manbalarga ko‘ra qadimgi odamlar xaqida noto‘g‘ri taxminlar qilishgan, yaʼni ularning faktlariga ko‘ra odam juda  Surg"),
        (13386, "Shuningdek, tana jaroxatlari, tabiiy ofatlar (yashin urishi, tog‘ ko‘chishi, sel) kabi omillar xam ularning xayotini qisqarishiga sabab bo‘lgan. Qadim Surg"),
        (13387, "Ularda organizm xaqida anotomik va fiziologik tasavvurlar bo‘lgan. Imperator qasridagilar uchun davolash muassasi bo‘lgan. U yerdagi shifokorlarni epi Surg"),
        (13388, "Qadimgi Xitoyda mandragora, opiy, gashishadan narkoz uchun foydalanilgan. Buning natijasida qorin va ko‘krak soxasidagi operatsiyalarga imkoniyat beri Surg"),
        (13389, "Xindiston jarroxlari qon chiqarish, amputatsiya, laparotomiya, kataraktani olish, yuzdagi defektlarni to‘g‘irlash uchun burun, lab, quloqlarni plastik Surg"),
        (13390, "Аssir-Vavilon jarroxligi kasallikni iblislar taʼsirida kelib chiqishi xaqidagi tasavvurlarga ega bulganlar. Shuning uchun ular tumor, yashash joyini e Surg"),
        (13391, "Qadimgi Misr jarroxligi o‘ziga xoslikka ega. Maʼlumki ularda o‘lganlarni balzamlash keng qo‘llanilgan. Bu esa o‘z navbatida anatomiyani rivojlanishiga Surg"),
        (13392, "Qadimgi Gretsiya, Аleksandriya va Rimdagi jarroxlik xozirgi zamonaviy jarroxlikning asosi deb xarakterlanadi. O‘sha davrni namoyondasi Gippokrat ilmiy Surg"),
        (13393, "Gippokrat shifokorlar obro‘sini oshirib, maktab yaratdi va shifokorlik qasamyodini qo‘lladi. Qadimgi Rim jarroxligi namoyondasi Galen gladiatorlar shi Surg"),
        (13394, "U 100dan ortiq ilmiy tibbiyot ishlari muallifi xisoblanadi. Uning 'Tib qonunlari' nomli 5 tomlik asari XVII asrlargacha Yevropadagi ko‘pgina tibbiy ma Surg"),
        (13395, "Tug‘ilish (uyg‘onish) davri (XV-XVII) cherkov xizmatchilarini ro‘li kamayishi bilan xarakterlanadi. Bu ilmni, sanʼatni, madaniyatni, tibbiyotni, shuni Surg"),
        (13396, "Vezaliy amaliy mashg‘ulot paytida o‘lik yorib o‘rganardi. Odam tanasi tuzilishi kitobi muallifidir. А. Vezaliy mushaklar, bug‘imlar, ichki organlar, s Surg"),
        (15730, "Ular o‘zlarining tashqi ko‘rinishlariga ayni e’tibor qaratadigan davrda bu holat ular uchun juda noxushlik tug‘diradi. Kasallikning rivojlanishida org Derm"),
        (15731, "NAZARIY QISM Akne - keng tarqalgan kasalliklardan biri bo‘lib, dunyo aholisining 90- 95 foizi hayotida bir marta bo‘lsada bu muammo bilan duch keladi  Derm"),
        (15732, "(Potekayev N. N., Oddiy husnbuzar (acne vulgaris) - ter bezlari va periglandular to‘qimaning surunkali polimorf multifaktor yallig‘lanish kasalligi bo Derm"),
        (15733, "Kaft, tovon va tovon yuzida ter be’zlari yo‘q. Uch turdagi ter be’zlari farqlanadi: mo‘ysimon, soch follikulalari bilan bog‘langan bo‘lib ular ildizig Derm"),
        (15734, "Shuning uchun yuqoridagi sohalar seboreyali sohalar deyiladi. bo‘g‘liq. Ular o‘lcham jihatdan katta bo‘lib, murakkab uzum shingili shakliga ega. Asosa Derm"),
        (15735, "Rasm Bir bo‘lakchali ТВ Rasm Ko‘p bo‘lakchali ТВ yoki unga yaqin joyda joylashadi. Bu turdagi ТВ lari quyidagi sohalarda uchraydi, peshona terisi, bur Derm"),
        (15736, "Har bir tugash qismida o‘zining chiqaruv yo‘liga ega bo‘lib, ular oxir oqibat soch follikulasi ildiziga ochiladi. TBda sekret bezli epiteliydagi sebot Derm"),
        (15737, "Keyinchalik yorilgan sebotsitlar va ularning mahsulotlari teri yog‘ini hosil qilib, u ТВ chiqaruv yo‘liga tomon siljiydi. ТВ gollokrin sekretsiyaning  Derm"),
        (15738, "N., . ТВ ni sekreti ajralishi sochni ko‘taradigan mushagi orqali amalga oshadi. Hayot davomida TBIari o‘z hajmini o‘zgartiradi. Ularning kattalashishi Derm"),
        (15739, "Yosh o‘tishi bilan ayollarda ter yog‘i ajralishi kamayishi kuzatiladi, lekin uning davomiyligi erkaklarda nisbatan uzoq davom etadi (Potekayev N.N., . Derm"),
        (15740, "Chigallar tarkibiga vegetativ nerv tizimi tolalari kiradi. Teri yog‘ini sekretsiyasi gormonal va neyrogen mexanizmlar orqali boshqariladi. Ter yog‘ini Derm"),
        (15741, "Ter be’zlari sekretsiyasisini adrenokortikotrop, kortikosteroid va androgen gprmonlari ko‘paytirib, esterogen gormoni esa sekretsiyani kamaytiradi. Se Derm"),
        (17046, "Yurtimizning tabiiy sharoiti, odamlarning turmush tarzi va boshqa bir qancha omillar sabab aholi orasida buyrak kasalliklaridan aziyat chekish holati  Nephro"),
        (17047, "Ularning etiologiyasi, patogenetik mexanizmi va klinik kechishi turli xil, ammo barchasi buyrak yetishmovchiligi bilan tugallanadi. Kasalliklarda asor Nephro"),
        (17048, "Buyrak yetishmovchiligi belgilari aniqlanganda yoki xavf omillari aniqlanganda, darhol shifokor bilan bog’lanish va tegishli davolanishni boshlash jud Nephro"),
        (17049, "Ammo surunkali buyrak kasalligi bilan og‘rigan ko‘plab odamlar uzoq vaqt davomida kasal bo‘lib qolishlarini bilishmaydi. Buyrak kasalliklari uzoq yill Nephro"),
        (17050, "Kasallikning ushbu bosqichida jiddiy shikoyatlar paydo bo‘ladi, ammo uni qaytarish yoki hech bo‘lmaganda uning rivojlanishini sekinlashtirish kerak. D Nephro"),
        (17051, "Aholining buyrak kasalliklarining xavf omillari to‘g‘risida xabardorligi va ehtiyotkorligi pastligicha qolmoqda, shu sababli kasallik kech bosqichda a Nephro"),
        (17052, "Siydik ajralishining buzilishi. Buyraklar- juft a’zo bo‘lib, asosiy faoliyati organizmdan chiqarilishi zarur bo‘lgan metabolizm mahsulotlarini va yot  Nephro"),
        (17053, "Chap buyrakning yuqori qutbi XI ko‘krak umurtqasi sathida, pastki qutbi esa 2 va 3 bel umurtqalari orasiga to‘g‘ri keladi. O‘ng buyrak chapiga nisbata Nephro"),
        (17054, "Chap buyrak oshqozon, taloq ya yo‘g‘on ichakning pastga tushuvchi qismi bilan yondoshadi. Ko‘ndalang chambar ichak tutqichlarining ildizi buyrakni o‘r Nephro"),
        (17055, "Kanalcha shartli ravishda uch qismga bo‘linadi: 1 tartibdagi proksimal egri kanalcha; Genle qovuzlog‘i; II tartibdagi distal egri kanalcha; Genle qovu Nephro"),
        (17056, "Suv va past molekulali moddalaming qon plazmasidan qobiq bo‘shlig‘iga filtratsiyasi koptokcha yoki glomerulyar filtr orqali amalga oshadi . Glomeralya Nephro"),
        (17057, "Shunday qilib, birlamchi siydikning tarkibi glomeralyar filtr xususiyatlariga bog‘liq. Me’yorida suv bilan birga oqsillarning ko‘pgina qismi va qonnin Nephro"),
        (20306, "1997- yilda “Qandli diabetda ko‘z kasalliklari tarqalishi klinikasi va epidemiologiyasi “ mavzusida nomzodli dissertatsiyasini himoya qilgan. Maxsus i Ophth"),
        (20307, "Oftalmolog magistrlar tayyorlash normativ va huquqiy hujjatlari muallifi. O‘zbekistonda birinchi ruscha va o‘zbekcha elektron multimeidal o‘quv qo‘lla Ophth"),
        (20308, "Oliy ta’lim rektorlar rayosatida oftalmologiya bo‘yicha monotemstik komissiya raisi. N.R.Yangieva mudirlik qilayotgan kafedra o‘qish jarayonida Respub Ophth"),
        (20309, "O‘zbekiston Respublikasi ixtisoslashgan ko‘z mikroxirurgiya markazi direktori, tibbiyot fanlari doktori (Xususiy “ Sihat farog‘at” klinikalarini zamon Ophth"),
        (20310, "2002 -yil tibbiyot falsafa doktori va 2016- yilda “ Katta yoshdagi kishilardagi makulodistrofiya” mazusida tibbiyot fanlari doktori dissertatsiyasini  Ophth"),
        (20311, "1965- yilda tashkil bo‘lgan bu bo‘lim tom ma’noda oftalmoonkologiya bo‘yicha ilmiy- amaliy markaz bo‘lib xizmat qiladi. Z.C. Islamov ko‘z qovoqlari, o Ophth"),
        (20312, "Respublika bo‘ycha barcha oftalmoonkologik bemorlar mana shu markazda davo topadilar. Siddikov Zafar Umarovich-tibbiyot fanlari nomzodi, Rossiya –Qozo Ophth"),
        (20313, "Termizda va Xorazmda mikroxirurgiya markazlarining filiallari tashkilotchisi. Barcha viloyat ko‘z klinikalarini diagnostik ISUZU avtobusi bilan ta’min Ophth"),
        (20314, "2 ta doktorlik dissertatsiyaga rahbarlik qilgan. Rustamov Sultonmurod Sa’dullaevich- 2018-yilda Shaxrizabz tuman oftalmologiya shifoxonasida ishlasa h Ophth"),
        (20315, "Qandli diabetda ko‘zdagi diabetik retinopatiyaning respublikada tarqalish epidemiyologiyasi, davolash va diagnostikasi algoritmini yaratgan Zaxidov Ul Ophth"),
        (20316, "Zakirxo‘jaev Rustamjon Asralovich- tibbiyot fanlari doktori, Tibbiyot akademiysining dekani. Bolalarda tug‘ma ko‘z kasalliklari diagnostikasi , tarqal Ophth"),
        (20317, "64 ta ilmiy ishlar muallifi. Respublikada novaskulyar glaukomani davolash prinsiplariga asos solgan eng yosh olima. .Fayzeva Umida Sanatovna tibbiyot  Ophth"),
        (21128, "Zararli omillar, jumladan, kimyoviy, ekologik, radiatsion ta’sirlar miqdori ortib bormoqda. Organizmning immunologik himoyasi buzilishi muhim ahamiyat Onco"),
        (21129, "Mamlakatimizda tibbiyot sohasini rivojlantirish, xususan, kasalliklarga erta tashxis qo‘yish, davolash va oldini olish usullarini takomillashtirishga  Onco"),
        (21130, "Tadqiqotining vazifalari: tekshirilgan aholi orasida teri saratoni va saraton oldi kasalliklarining tarqalishini baholash; aholi orasida yaxshi va yom Onco"),
        (21131, "Dissertatsiyada quyidagi tekshiruv usullari qo‘llanildi: bajarishda retrospektiv tadqiqotlar, istiqbolli tadqiqotlar. Tadqiqotining ilmiy yangiligi qu Onco"),
        (21132, "Tadqiqotining natijalarining ilmiy va amaliy ahamiyati. Olingan natijalarning ilmiy ahamiyati tadqiqot ma’lumotlarini kompleks baholash va taqqoslashd Onco"),
        (21133, "Tadqiqotining natijalarining joriy qilinishi. Teri o‘smalarini tashxislash bo‘yicha olingan ilmiy natijalar asoslida: birinchi ilmiy yangilik sanoat v Onco"),
        (21134, "Xulosa: teri o‘smalarini erta tashxislashning yangi usuli yordamida har bir bemor uchun tejalgan mablag‘ 809000 so‘mni tashkil etgan. ikkinchi ilmiy y Onco"),
        (21135, "Ilmiy yangilikning ijtimoiy samaradorligi: teri o‘smalarini davolashning ishlab chiqilgan kombinirlangan usulidan foydalanish jarrohlik aralashuvisiz  Onco"),
        (21136, "Ushbu tadqiqot natijalari 3 ta ilmiy-amaliy anjumanlarda, jumladan, 2 ta xalqaro va 1 ta respublika miqyosidagi ilmiy-amaliy anjumanlarda muhokama qil Onco"),
        (21137, "Dissertasiya tarkibi kirish, besh bob, xotima, amaliy tavsiyalar, xulosalar va foydalanilgan adabiyotlar ro‘yxati, ilovalardan iborat. Dissertasiya ha Onco"),
        (21138, "Dissertatsiyaning «Klinik materiallar va tadqiqot usullarining umumiy tavsifi» ikkinchi bobida klinik materialning umumiy tavsifi va laboratoriya tadq Onco"),
        (21139, "Tibbiyot xodimlari uchun biz tomonidan ishlab chiqilgan so‘rovnoma va eslatmani joriy qilish natijasida 4200 kishi tekshirildi(Olmaliq shahrida 2200,  Onco"),
        (25132, "Ilmiy- texnika taraqqiyoti xalq farovonligini oshirish va inson umrini uzaytirish bilan birga dunyo ahli oldiga sanoat chiqindilari, ko‘p sonli avtotr Pulm"),
        (25133, "AQSHda har besh kishidan bittasi o‘pka kasalliklariga chalingan, ulardan esa har yili o‘rta hisobda 240 ming kishi hayotdan ko‘z yummoqda. MDH va uzoq Pulm"),
        (25134, "So‘nggi yillarda ko‘pgina yosh ishchilar va xizmatchilar kasallik vajidan o‘z kasb-korlari bilan shug‘ullana olmayaptilar. Masalan, AQSHda nogironlikn Pulm"),
        (25135, "Kasallanish esa so‘nggi besh yil ichida 2,5-marta oshgan. Bronxial astma va surunkali bronxit bilan kasallanish ayniqsa tez sur’atlar Kitobxon. Com bi Pulm"),
        (25136, "Respublika bo‘yicha 15-17 yoshli yigit - qizlar orasida nafas a’zolari kasalliklariga duchor bo‘lgan bemorlar, hazm a’zolari kasalliklari bilan xastal Pulm"),
        (25137, "Nafas a’zolari kasalliklari bo‘yicha standartlangan o‘lim koeffitsiyenti (SO‘K) ayollarga nisbatan, erkaklarda 1,67-marta ortiq (Ovro‘po bo‘yicha bu k Pulm"),
        (25138, "Yuqorida qayd etilgan ko‘rsatkich Qoraqalpog‘iston Respublikasi, Toshkent, Navoiy viloyatlarida va Toshkent shahrida boshqa viloyatlarga qaraganda anc Pulm"),
        (25139, "Shunga qaramay joylarda pulmonologlarni tayyorlash ishiga e’tibor o‘z o‘rnida emas. Respublikada pulmonolog vrachlarning yetishmasligi va umumiy amali Pulm"),
        (25140, "Ftiziatriya va pulmonologiya ilmiy tekshirish instituti, Toshkent vrachlar malakasini oshirish instituti pulmonologiya va klinik allergologiya kafedra Pulm"),
        (25141, "Bizning ma’lumotlarimizga binoan, O‘zbekiston mintaqalarida nospesifik o‘pka kasalliklarining tarqalishi turlicha. Masalan, ekologik sharoiti yomon, p Pulm"),
        (25142, "Ismoilov, . Surunkali nospesifik o‘pka kasalliklari bilan dunyodagi boshqa mamlakatlarda asosan erkaklar xastalanganligi kuzatilsa, bizda mazkur jaray Pulm"),
        (25143, "Kamqon, kam quvvat onalardan tug‘ilgan nosog‘lom bolalar go‘daklikdan o‘tkir respirator kasalliklar, o‘tkir bronxit va zotiljamga chalinuvchan bo‘lish Pulm"),
        (25158, "XIX asrning oxiri va XX asr boshlarida fizika va kimyo fanlari sohasida olamshumul yangiliklar qo‘lga kiritilib, bu tibbiyot fanining ham rivojlanishi Radiol"),
        (25159, "Birinchi davr 1895 - 1920-yillarni o‘z ichiga oladi. 1895-yilda nemis olimi, professor Vilgelm Konrad Rentgen “X” nurlarini kashf etadi va dunyoda fiz Radiol"),
        (25160, "Zamondoshlari va shogirdlarining aytishicha ulug‘ olim kamtar, insofli va mehnatsevar, lekin kam muloqotli, badjahl, odamovi va prinsipial inson bo‘lg Radiol"),
        (25161, "V.K.Rentgen o‘rta ma’lumot olmagan, chunki u bir o‘rtog‘ining qilmishlari uchun gimnaziyadan haydalgan. Yetuklik shaxodatnomasini olishga xarakat qilg Radiol"),
        (25162, "Lekin bo‘lg‘usi qaylig‘ining aqlliligi tufayli Vil‘gelm Konrad V.K.Rentgen astoydil o‘qishga kirishadi. Rentgen (1845- 1868-yili 24 yoshida institutni Radiol"),
        (25163, "Kundt Vyursburgga ko‘chgandan so‘ng Rentgen ham o‘sha shaharga ko‘chadi. Shunday qilib, ularning do‘stligi va hamkorligi boshlanadi. V.K.Rentgen yunon Radiol"),
        (25164, "Ammo konservativ niyatda bo‘lgan Vyursburg universitetining akademiklik doirasida bunga qarshilik qilishadi. Agar V.K.Rentgen professorlikka saylanmas Radiol"),
        (25165, "1888-yilda Vyursburg universitetidan atoqli fizik Kolraush ketishi munosabati bilan u kafedra mudiri lavozimidan ozod qilinadi va professorlik lavozim Radiol"),
        (25166, "V.K.Rentgen eng yaqin do‘sti va ustozidan ajraladi. Ko‘p vaqt o‘tmay V.K.Rentgen Vyursburgdagi fizika institutiga direktor qilib tayinlanadi va bu yer Radiol"),
        (25167, "1895-yil 8-noyabr oqshomida V.K.Rentgen katod nuri ustida tajriba o‘tkazadi. Qorong‘i sharoitda har gal katod nurini ulaganida u bariy platinosianid b Radiol"),
        (25168, "Laboratoriyaga yig‘ma karavot qo‘yib, yetti hafta hech qayerga chiqmaydi. Bir necha bor o‘tkazilgan tajribalar natijasida Rentgen elektr tokiga ulanga Radiol"),
        (25169, "Navbatdagi tajribalarida noma’lum nurning metalldan ishlangan yupqa plastinkadan o‘tolmasligini aniqdaydi. Turli metalldan ishlangan bir xil qalinlikd Radiol"),
        (25820, "Kеyingi 20 yil davomida ortopеdiya va travmatologiya sohasida bolalarda uchraydigan jaroxatlar, tayanch-harakat tizimining tug‘ma va orttirilgan nuqso Rheum"),
        (25821, "Darslikni yaratishda mualliflar Toshkеnt pеdiatriya tibbiyot instituti bolalar travmatologiyasi va ortopеdiyasi kafеdrasining klinikasida dеyarli 30 y Rheum"),
        (25822, "Bunda tayanch a‘zolarining tug‘ma kasalliklari etiologiyasi, patogеnеzi va bolaning yoshiga bog‘liq holda o‘zgarib boruvchi klinikasi yoritilgan. Klin Rheum"),
        (25823, "Darslik asosan umumiy amaliyot shifokori - bakalavrlar uchun mo‘ljallangan bo‘lib, unda travmatologik va ortopеdik xastaliklarni o‘z vaqtida aniqlash  Rheum"),
        (25824, "TRAVMATOLOGIY VA ORTOPЕDIYA FANINING MAQSADI Tibbiyot haqidagi adabiyotlarga “ortopеdiya” so‘zini birinchi marta farang shifokori Nicolas Andry kiritg Rheum"),
        (25825, "Masalan, ingliz adabiyotlarida orthos — to‘g‘ri va paes — oyoq panjasi, ya‘ni, oyoqning to‘g‘ri o‘sishini o‘rganuvchi fan sifatida tushuntirilgan. Ita Rheum"),
        (25826, "Ilgari ortopеdiyada faqat tayanch-harakat a‘zolari nuqsonlariga davo qilishgan bo‘lsa, hozirgi vaqtda esa davolashning dastlabki kunidan boshlab, jaro Rheum"),
        (25827, "Jarohatlanish kishi hayoti davomida turli sabablarga ko‘ra yuzaga kеladigan baxtsiz voqеlik ko‘rinishi bo‘lib, uni asosan umumiy jarrohlar davolaganla Rheum"),
        (25828, "Ortopеd-travmatologik bеmorlarga jarohatlangan yoki xastalangan kundan boshlab davo qilinishi natijasida ular tеz kunda sog‘ayib, mеhnat qobiliyatlari Rheum"),
        (25829, "Ortopеdik profilaktika xastaliklarning kеlib chiqishi va rivojlanishi haqida ogohlantiradi. Masalan, ortopеdik xastaliklarning oldini olish bola qomat Rheum"),
        (25830, "Masalan, son suyagining tug‘ma chiqishini erta aniqlab, davo muolajalarini o‘z vaqtida qo‘llash tananing shakliy o‘zgarishlari oldini oladi. Ortopеdla Rheum"),
        (25831, "Shu maqsadda xastaliklarni davolashda eng avvalo uning funksional holatini tiklash zarur. Buning uchun dori-darmonlar bilan birgalikda uqalash muolaja Rheum"),
        (30173, "Hozirda dunyo tajribasiga ko‘ra Karlsrue ilmiy tadqiqot markazi va amaliy informatika instituti (Forschungszentrum Karlsruhe, Insitut für Angewandte I Anesth"),
        (30174, "“Ta’lim tizimini rivojlantirish orqali o‘quvchilarni zamonaviy bilim va ko‘nikmalarga o‘rgatish”1 muhim ustuvor vazifa sifatida belgilangan. Bu borada Anesth"),
        (30175, "Tadqiqotning respublika fan va texnologiyalari rivojlanishi ustuvor yo‘nalishlariga mosligi. Mazkur tadqiqot respublika fan va texnologiyalarni rivojl Anesth"),
        (30176, "Mamlakatimizdagi oliy ta’lim tizimida yoshlarning ma’naviy barkamolligini ta’minlash, kasbiy faoliyatga yo‘naltirish, ta’limga zamonaviy yondashuvlarn Anesth"),
        (30177, "Tadqiqotchi N.Ahmedova bo‘lajak shifokorlarda kasbiy-ma’naviy fazilatlarni tarbiyalash tizimini rivojlantirish masalalarini yoritgan. Mamlakatimiz tib Anesth"),
        (30178, "Tibbiy ta’lim tizimini isloh qilish vazifalaridan kelib chiqqan holda ta’lim jarayonida zamonaviy o‘quv-texnik vositalari, birinchi navbatda kompyuter Anesth"),
        (30179, "Tadqiqotning maqsadi anesteziologiya va reanimatologiya fani doirasida imitatsion ta’lim texnologiyalarini rivojlantirish bo‘yicha uslubiy va amaliy t Anesth"),
        (30180, "Tadqiqotning usullari. Tadqiqоtda qiyosiy tahliliy o‘rganish, mоdеllashtirish, ankеta sо‘rоvlari, tеstlar, kuzatuv, pеdagоgik kuzatish, suhbat, intеgr Anesth"),
        (30181, "Tadqiqot natijalarining ishonchliligi ishda qo‘llangan yondashuv va usullar, uning doirasida foydalanilgan nazariy yondashuvlar rasmiy manbalardan oli Anesth"),
        (30182, "Tadqiqot natijalarining joriy qilinishi. Tibbiy ta’lim talabalarini anesteziologiya va reanimatologiya fanini o‘qitishda imitatsion ta’lim texnologila Anesth"),
        (30183, "Natijada tibbiyot oliy o‘quv yurtlari talabalarining kasbiy faoliyatga yo‘naltirilgan mavzular mazmunini o‘rganishning shart sharoitlari takomillashti Anesth"),
        (30184, "Monografiya mavzusi bo‘yicha jami 24 ta ilmiy ish chop etilgan, 1 ta o‘quv qo‘llanma, 1 ta elektron o‘quv qo‘llanma. O‘zbekiston Respublikasi Oliy att Anesth"),
        (30462, "Yuqori qismi og‘iz bo‘shlig‘i a’zolari, pastki qismi esa qizilo‘ngach, mye’da, jigar, o‘t yo‘llari va me’da osti bezi kabi a’zolardan tuzilgan. Rentge GI"),
        (30463, "Shuning uchun bu a’zolarga katta ahamiyat berish va ularni sinchiklab o‘rganish kerak. Ovqat hazm qilish a’zolari anatomik tuzilishi jihatdan atrofida GI"),
        (30464, "KONTRAST MODDALAR VA ULARNING QO‘LLANISHI Ovqat hazm qilish a’zolarini rentgenologik tekshirish uchun atom og‘irligi past havo, kislorod, karbonat ang GI"),
        (30465, "Eng xarakterliga, bariy sulfat aralashmasining me’da-ichak yo‘lida surilishi va bo‘shashi, oddiy ovqat qabul qilgandek, bir vaqtda o‘tadi. Standart ba GI"),
        (30466, "So‘ngra 100 g bariyni 80 ml suvda aralashtirib qaynatiladi, natijada bir xil emulsiya hosil bo‘ladi, u me’da-ichak yo‘lini rentgenda ko‘rish uchun ich GI"),
        (30467, "T.N. Ilyosov, N.A. Eshmuhamedov tavsiya etgan aralashtirgich (227-rasm) oddiy tipda ishlangan bo‘lib, undan barcha rentgen xonalarida foydalanish mumk GI"),
        (30468, "227-rqam. Bariy sulfat aralashmasini maydalaydigan aralashtirgich: 1-ustuncha asosi;2- aylanish tezligi o‘zgartiruvchi va o‘lchovchi;3-butulka surilis GI"),
        (30469, "Bariy sulfat aralashmasi iliq holatda 37°C haroratda qo‘llaniladi. Gaz (kislorod, havo, karbonat angidrid gazi)dan qizilo‘n- gachni, mye’da gumbazi de GI"),
        (30470, "Shuning uchun hamma nur bilan tekshirish usullarini: rentgenologik, radionuklid va ultratovush usullariga bo‘lish mumkin. Ovqat hazm qilish a’zolarini GI"),
        (30471, "Hammabop, klassik usullar - rentgenoskopiya va rentgenografiyadan boshlanadi. Rentgenoskopiya ko‘p holatda tekshirilayotgan a’zo funksiyasi va morfolo GI"),
        (30472, "Rentgenografiya- rentgenogramma olish usuli. Rentgenogramma aniq tasvirga va axborotga ega. Suratlar mo‘ljalli va umumiy bo‘lishi mumkin. TISH VA JAG‘ GI"),
        (30473, "Bu usullar yordamida qilinayotgan davolash muolajalarining nafiga baho berish va kasallikning kyechishini o‘rganish mumkin. Stomatologiya amaliyotida  GI"),
        (32381, "Jahondagi barcha mamlakatlarda demografik ko’rsatkichlar qariyalar hisobiga oshib bormoda. Bu esa 'Gerontologiya' va 'Geriatriya' sohasidagi bilimlar  Gero"),
        (32382, "Gerogigiyena. Gerontopsixologiya. Gerodermiya. Gerodietetika. Gero"),
        (32383, "Geroekologiya. Keksalik umrning qonuniy tarzda yuz beradigan yakunlovchi davridir. Biroq muddatidan oldin qarish hodisasi ham hayotda bor haqiqatdir.  Gero"),
        (32384, "P. Botkin va I. I. Mechnikovlar fiziologik va barvaqt qarish mavjudligi haqidagi tushunchalarni yoqlab chiqqanda haq edilar. Gero"),
        (32385, "Barvaqt qarish boshdan kechirilgan kasalliklar yoki tashqi muhitning zararli omillari ta’sirida yosh bilan bog’liq o’zgarishlarning bir muncha erta ri Gero"),
        (32386, "Qarish - qarilik, ya’ni yosh ulg’aya borishi bilan organizmda paydo bo’ladigan o’zgarishlarning qonuniy tarzda ro’y berish jarayonidir. Umuman olganda Gero"),
        (32387, "Gerogigiyena esa keksaygan va katta yoshdagi kishilar gigienasini o’rganmoqda. 'Gerontopsixologiya' keksalar ruhiy holati va fe’l-atvorini; 'Gerodiete Gero"),
        (32388, "Agar bu taxmin tasdiqlansa, 'Gerontologiya' fanida keskin o’zgarishlar yuz berishi va insonning hozirdan ham uzoqroq umr ko’rishiga erishiladi. Geneti Gero"),
        (32389, "Uning ildizlari juda qadimdan boshlangan bo’lib, qadimiy xitoy va hind olimlari asarlarida, Gippokrat to’plamlarida hamda Ibn Sinoning 'Tib qonunlari' Gero"),
        (32390, "I. Mechnikov qarish jarayonini hujayralararo muntazam aloqalarning buzilishi va organizmda intoksikatsiya oqibatida metabolitlarning to’planishi bilan Gero"),
        (32391, "Pavlov esa oliy nerv faoliyatidagi o’zgarishlarning qarish jarayoniga ta’sirini o’rgangan. A.A. Bogomoles qarish jarayonini biriktiruvchi to’qima stru Gero"),
        (32392, "Respublikamizning yetuk olimlaridan biri bo’lgan professor R.M. Nurmuhammedovning yoshi ulg’aygan kishilardagi oshqozon-ichak tizimi kasalliklarini ja Gero"),
        (33822, "Atrof-muhit va ishlab chiqarish omillari ta’sirida yu- zaga keladigan karlik, quloq, tomoq va burun a’zolarining allergik holatlarini, plastik jarrohl ENT"),
        (33823, "Unda LOR a’zolari faoliyati buzilganda va LOR kasalliklarida bemorlarni kuzatish va parvarishlashga oid amaliy ko‘nikmalarni o‘zlashtirishga e’tibor q ENT"),
        (33824, "Shuning- dek, Yu.M. Ovchinnikov va S.V.Morozovalarning 2002-yil Moskva «Masterstvo» nashriyoti tomonidan tibbiyot kollej lari uchun chop etilgan «Otor ENT"),
        (33825, "Tabobat muvaffaqiyatlarni qo‘lga kiritishda og‘ir va mashaqqatli yo‘lni bosib o‘tdi. Har qaysi zamon tabo batidan turli kasalliklarni davolashga doir  ENT"),
        (33826, "Suqrot asarlarida tomoq, burun va quloq kasalliklarini davolash haqida birmuncha aniq ma’lumotlar berilgan. Olim suyakli chig‘anoq ichida pardali chig ENT"),
        (33827, "Taniqli olim Sels quloq kasalliklari ko‘z kasalliklariga qaraganda ancha xatarli kasallik ekanini, agar vaqtida oldi olinmasa, salbiy oqibatlarga saba ENT"),
        (33828, "Uning ana shu a’zolar anatomiyasi va fiziologiyasiga oid ta’riflari hozir ham o‘z ahamiyatini yo‘qotmagan. O‘sha davrga oid ma’lumotlar, asosan, quloq ENT"),
        (33829, "Chunonchi, Fallopiy (1513–quloq labirintini bayon qilgan. Bu kanal olim nomi bilan ataladigan bo‘ldi. Yev- staxiy (u 1570-yilda vafot etgan) nog‘ora b ENT"),
        (33830, "1683-yilda Dyu Varne birinchi mar- ta chig‘anoq tuzilishini kashf etib, uni cholg‘u asbobiga o‘xshatdi. U asosiy membrana turli uzunlikda bo‘lgani uch ENT"),
        (33831, "Shuningdek, quloq kasalliklarida jarrohlik davo yo‘llarini ham qo‘llashni tav- siya qilgan. Chunonchi, 1649-yilda Riolan eshituv nayi berkilib qo lish ENT"),
        (33832, "1890-yilda Kuper birinchi marta parasentez o‘rta quloq yallig‘langanda nog‘ora pardani operatsiya qilishni taklif qilgan. Rossiyada nashr qilingan «Ja ENT"),
        (33833, "Shuningdek, ko‘pgina quloq, tomoq va burun kasalliklarini konservativ va jarrohlik yo‘li bilan davolashga oid tavsiyalar bergan. Ko‘rinib turibdiki, t ENT"),
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
