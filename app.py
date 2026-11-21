from flask import Flask, render_template, request
import joblib
import pandas as pd

app = Flask(__name__)

# Eğitilmiş modeli ve sütun listesini yüklüyoruz
model = joblib.load('valorant_ajan_modeli.pkl')
ozellik_sutunlari = joblib.load('model_sutunlari.pkl')

# Harita ve ajan listelerini modelden otomatik alıyoruz
HARITALAR = sorted([c.replace('Map_', '') for c in ozellik_sutunlari if c.startswith('Map_')])
AJANLAR = sorted([c.replace('A_', '') for c in ozellik_sutunlari if c.startswith('A_')])

def ajan_oner(harita, bizim_ajanlar, rakip_ajanlar, top_n=5):
    aday_ajanlar = [a for a in AJANLAR if a not in bizim_ajanlar]
    sonuclar = []

    for aday in aday_ajanlar:
        girdi = pd.DataFrame(0, index=[0], columns=ozellik_sutunlari)

        if f'Map_{harita}' in girdi.columns:
            girdi[f'Map_{harita}'] = 1

        for ajan in bizim_ajanlar + [aday]:
            if f'A_{ajan}' in girdi.columns:
                girdi[f'A_{ajan}'] = 1

        for ajan in rakip_ajanlar:
            if f'B_{ajan}' in girdi.columns:
                girdi[f'B_{ajan}'] = 1

        olasilik = model.predict_proba(girdi)[0][1] * 100
        sonuclar.append({'ajan': aday.capitalize(), 'oran': round(olasilik, 2)})

    sonuclar.sort(key=lambda x: x['oran'], reverse=True)
    return sonuclar[:top_n]

@app.route('/', methods=['GET', 'POST'])
def index():
    oneriler = None
    hata = None
    secilen_harita = HARITALAR[0] if HARITALAR else ''
    bizim_secimler = ['', '', '', '']
    rakip_secimler = ['', '', '', '', '']

    if request.method == 'POST':
        secilen_harita = request.form.get('harita', '')
        bizim_secimler = [request.form.get(f'bizim_{i}', '') for i in range(1, 5)]
        rakip_secimler = [request.form.get(f'rakip_{i}', '') for i in range(1, 6)]

        bizim_temiz = [a for a in bizim_secimler if a]
        rakip_temiz = [a for a in rakip_secimler if a]

        if len(set(bizim_temiz)) != len(bizim_temiz):
            hata = "Kendi takımında aynı ajanı birden fazla kez seçemezsin."
        elif len(set(rakip_temiz)) != len(rakip_temiz):
            hata = "Rakip takımda aynı ajanı birden fazla kez seçemezsin."
        elif len(bizim_temiz) < 4:
            hata = "Öneri alabilmek için kendi takımından 4 ajan seçmelisin."
        else:
            oneriler = ajan_oner(secilen_harita, bizim_temiz, rakip_temiz, top_n=5)

    return render_template(
        'index.html',
        haritalar=HARITALAR,
        ajanlar=AJANLAR,
        oneriler=oneriler,
        hata=hata,
        secilen_harita=secilen_harita,
        bizim_secimler=bizim_secimler,
        rakip_secimler=rakip_secimler
    )

if __name__ == '__main__':
    app.run(debug=True)