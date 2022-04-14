# Metalliosien_mittaus
Tämä repo sisältää Laaki-hankkeessa toteutetun sylinterimäisten metalliosien mittauksen kuvien perusteella. Mittausskriptit on tehty Python-ohjelmointikielellä, ja niissä hyödynnetään [OpenCV-kirjastoa](https://opencv.org/). Tulokset kirjoitetaan [Pandas-kirjaston](https://pandas.pydata.org/) avulla.

Laaki (Laadusta kilpailukykyä konenäöllä) on Seinäjoen ammattikorkeakoulun vuosina 2020 - 2022 toteuttama hanke, joka keskittyy automaattiseen konenäöllä suoritettavaan laadunvalvontaan ja sen hyödyntämiseen Etelä-Pohjanmaan pk-teollisuudessa. Tarkempaa tietoa [hankkeen kotisivuilla](https://projektit.seamk.fi/alykkaat-teknologiat/laadusta-kilpailukykya-konenaolla-laaki/).

Esitetyt mittausskriptit demonstroivat konenäön käyttö metalliteollisuuden mittauksissa. Esimerkkikappaleet ovat sylinterimäisiä metallisia koneenosia, ja 

![Yleiskuva metalliosista](/doku_kuvat/yleiskuva_osat.png)

## Käyttö

Seuraavia ohjeita noudattamalla saat luotua kehitysympäristön koodille ja ajettua sitä omalla koneellasi.

### Esivaatimukset

Ainoa pakollinen esivaatimus on asentaa
- [Python 3.X](https://www.python.org/downloads/). Kehittäessä käytetty versio oli 3.9.5.

### Kehitysympäristön rakentaminen

On suositeltavaa käyttää virtuaaliympäristöä Python-projekteissa. On mahdollista myös lisätä Python path-ympäristömuuttujaan, jolloin erillistä virtuaaliympäristöä ei tarvita. Tällöin tosin kaikki asennettavat Python-moduulit asentuvat Pythonin asennushakemistoon. Virtuaaliympäristö määritellään seuraavasti Windowsissa:

```
<pythonin_asennushakemisto>\python.exe -m venv <virtuaaliympäristön_nimi>
```

Komennon syöttämisen jälkeen kansio nimeltä <virtuaaliympäristön_nimi> ilmestyy hakemistoon, jossa komento ajettiin. Kloonaa ensin tämä repo ja luo sitten virtuaaliympäristö projektikansioon. Aktivoi virtuaaliympäristö.

Asenna seuraavaksi tarvittavat Python-moduulit komennolla

```
pip install -r requirements.txt
```

Nyt kaikki on asennettu.

### Tiedostot ja kansiot

**main.py** on pääohjelma. Se kutsuu muita Python-tiedostoja.

**mittaus.py** suorittaa mittaukset kuvista eli mittaa viisteen paksuuden ja sisähalkaisijan käyttämällä hyväkseen Houghin viivamuunnosta ja Houghin ympyrämuunnosta.

**kalibrointi.py** poistaa linssi- ja perspektiivivääristymän kuvasta käyttämällä kalibrointitiedostoa. Kalibroinnin voi tehdä dxf_contour_comparer-repossa olevalla calib_gui.py-ohjelmalla ja kameralla otetulla kuvalla shakkilaudasta.

**kuvat**-kansio sisältää esimerkkikuvia kahdeksasta metallisosasta. Kuvat on otettu ylhäältäpäin. Kansio sisältää myös kalibraatiotiedoston cal.json.

**doku-kuvat**-kansio sisältää tässä dokumentissa käytettävät kuvat.

### Ohjelman ajaminen

Kun **main.py** suoritetaan, aukeaa ikkuna, joka pyytää kansiota. Sille annetaan kansio "kuvat". Seuraavaksi aukeaa kalibraatiotiedosta pyytävä ikkuna. Sille annetaan tiedosto "cal.json". Alla esimerkki aukeavasta ikkunasta:

![Kuva ikkunasta](/doku_kuvat/ikkuna.png)

Tämän jälkeen ohjelma rullaa kaikki sille annetun kuvakansion alakansiot läpi. Ohjelma olettaa, että hakemistorakenne on seuraava:

<pre>
├── annettu_kuvakansio
│   ├── kappaleen1_nimi
│   |   ├── kuva1
│   |   ├── kuva2
|   |   |    ...
│   |   └── kuvan
|   |
│   ├── kappaleen2_nimi
│   ├── kappaleen3_nimi
|   |        ...
│   └── kappaleenm_nimi
</pre>

Annetun kuvakansion alla voi olla myös yksittäisiä tiedostoja (kuten cal.json) tai tuloskansio (oletuksena nimellä 'results' - nimen voi muuttaa tiedostossa **main.py**). Ohjelma olettaa kaikkien muunnimisten kansion sisältävän ylhäältä otettuja kuvia sylinterimäisistä metalliosista. Esimerkkikuva (tai sen ROI) alla. Kuvien korkeus voi olla joko 1200 tai 3000 (2 Mpix tai 12 Mpix). Tunnistuksessa käytettävät parametrit on asetettu näiden kuvakokojen mukaan. Itse asiassa fiksumpaa olisi suhteuttaa ne metalliosan kokoon kuvassa.

![Esimerkkikuva metalliosasta](/doku_kuvat/osa.JPG)

Kun ohjelma on rullannut kaikki kuvat läpi, se luo annettuun kuvakansioon alikansion 'results', joka sisältää samannimiset alikansiot kuin annettu kuvakansio alunperin. Näissä kansioissa on tuloskuvat samalla nimellä kuin alkuperäiset kuvat. Tuloskuviin on merkitty vihreällä vivalla löydetyt viisteet, sinisellä sisähalkaijan mittauksessa käytettävä sovitettu ympyrä ja valkoisella sekä vihreällä mittaustulokset.

![Esimerkki tuloskuvasta](/doku_kuvat/tulos.JPG)

Kuvakansioon luodaan myös tiedosto 'results.xlsx". Siinä yksittäisillä välilehdillä on esitettynä kunkin kansion kaikkien kuvien mittaustulokset (viisteiden paksuudet ja sisähalkaisijat) taulukkona sekä lopuksi niiden keskiarvot ja keskihajonnat. Välilehdet on nimetty samoin kuin kansiot. Lisäksi on välilehte "yht.veto", joka sisältää jokaisen kansion mittaustulosten keskiarvon ja keskihajonnan.

![Yksittäisen kansion tulokset](/doku_kuvat/excel1.JPG)
![Tulosten yhteenvetovälilehti](/doku_kuvat/excel2.JPG)
![Välilehdet](/doku_kuvat/excel3.JPG)
