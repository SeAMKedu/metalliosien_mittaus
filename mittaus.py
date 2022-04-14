import cv2
import numpy as np
from pandas import DataFrame
from os import listdir, makedirs
from os.path import join, exists
from pathlib import Path
from kalibrointi import calibrate_image

def calc_dist_p_line(x1, y1, x2, y2, px, py):
    """Laskee pisteen etäisyyden suorasta, joka on
    määritelty kahdella pisteellä.

    Args:
        x1 (float): Suoran ensimmäisen pisteen x-koordinaatti
        y1 (float): Suoran ensimmäisen pisteen y-koordinaatti
        x2 (float): Suoran toisen pisteen x-koordinaatti
        y2 (float): Suoran toisen pisteen y-koordinaatti
        px (float): Pisteen x-koordinaatti
        py (float): Pisteen y-koordinaatti

    Returns:
        float: Pisteen etäisyys suorasta
    """
    dist = np.abs(np.cross(np.array([x2, y2])-np.array([x1, y1]), 
                np.array([px, py])-np.array([x1, y1])) / 
                np.linalg.norm(np.array([x2, y2])-np.array([x1, y1])))
    return dist


def process_image_folder(folder, calib_data, show_imgs=False, 
                        res_folder=None):
    """Käsittelee kansiollisen kuvia, joissa on sylinterimäisiä metalliosia. 
    Osien sisähalkaisijat sekä niiden viisteiden paksuudet lasketaan ja 
    merkitään tuloskuviin. Tulokset palautetaan Pandas-dataframena, jossa on
    jokaisen kansion sisältämän kuvan nimi ja mittaustulokset sekä
    viimeisillä riveillä mittaustulosten keskiarvot ja keskihajonnat.

    Args:
        folder (string): Kuvakansion polku
        calib_data (dict): Kalibraatiodata (luettu json-tiedostosta)
        show_imgs (bool, optional): Näytetäänkö tuloskuvat ajon aikana. Defaults to False.
        res_folder (string, optional): Jos ei None, tuloskuvat talletetaan tänne. 
                                        Defaults to None.

    Raises:
        RuntimeError: Jos sisäympyrän mitoilla löytyy useampi ympyrä

    Returns:
        pandas dataframe: Mittaustulokset taulukkona
    """

    filelist = listdir(folder)
    
    # Tulokset per kuva
    dists1 = []
    dists2 = []
    diams = []

    params_2Mpix = {"minRadius":140, "maxRadius":160, "minPoints": 80}
    params_12Mpix = {"minRadius":340, "maxRadius":380, "minPoints": 150}

    # Käydään kuvat läpi tiedosto kerrallaan.
    for filename in filelist:
        ext = filename.split(".")[1]
        if ext == "jpg" or ext == "png" or ext == "bmp": # Hyväksytyt formaatit
            filepath = join(folder, filename)
            print(f"Processing image {filepath}")

            # Luetaan kuva ja poistetaan linssivääristymä
            img = cv2.imread(filepath)
            img = calibrate_image(img, calib_data)

            # Muutetaan harmaasävyksi, pehmennetään ja etsitään reunat
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            ksize = 3
            gray = cv2.medianBlur(gray, ksize)
            edges = cv2.Canny(gray, 100, 150)
            
            if show_imgs:
                cv2.imshow("reunat", cv2.resize(edges, (1600, 1200)))

            # Piirron parametrit
            line_width = round(img.shape[1] / 1600)
            font_face = round(img.shape[1] / 1600 * 0.75)

            # Analyysiparametrit kuvan koon mukaan
            rivit, sarakkeet = gray.shape # Tieto kuvan koosta
            if rivit == 1200:
                params = params_2Mpix
            elif rivit == 3000:
                params = params_12Mpix
            else:
                raise RuntimeError(f"Odottamaton kuvan koko {sarakkeet}x{rivit}. Tuetut koot: 1600x1200 ja 4096x3000.")

            # Etsitään sisäympyrä Houghilla
            circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1, 100, 
                                        param1=50, param2=30, 
                                        minRadius=params["minRadius"], 
                                        maxRadius=params["maxRadius"])

            # Pitäisi löytyä vain yksi ympyrä
            if circles is not None:
                if len(circles) > 1:
                    raise RuntimeError("Parametreilla löytyi useampi ympyrä")
                c = circles[0][0]
                
                # Lasketaan halkaisija millimetreissä ja lisätään listaan
                diam = c[2]*2 / calib_data["ppmm"]
                diams.append(diam)

                # Pyöristetään kokonaislukuihin ja piirretään
                cints = np.uint16(c)
                cv2.circle(img, (cints[0], cints[1]), cints[2], (255, 0, 0), line_width)
                cv2.circle(img, (cints[0], cints[1]), 2, (255, 0, 0), 3*line_width)
                cv2.putText(img, f"halk.: {diam:.2f} mm", (cints[0] + 10, cints[1]), 
                            cv2.FONT_HERSHEY_SIMPLEX, font_face, (255, 255, 255), line_width)
            else:
                diams.append(None)

            # Houghin viivamuunnoksen parametrit
            rho_reso = 1 # Yhden pikselin tarkkuus
            theta_reso = np.pi / 180 # Asteen tarkkuus
            min_pisteet = params["minPoints"] # Suoran toteuttavat pisteet

            suorat = cv2.HoughLines(edges, rho_reso, theta_reso, min_pisteet)

            lavistaja = int(np.sqrt(rivit**2 + sarakkeet**2))

            if suorat is not None:
                s_info = [] # Tänne suoran tiedot
                for s in suorat:
                    rho, theta = s[0]
                    a = np.cos(theta)
                    b = np.sin(theta)
                    x0 = a*rho
                    y0 = b*rho
                    x1 = int(x0 + lavistaja * (-b))
                    y1 = int(y0 + lavistaja * a)
                    x2 = int(x0 - lavistaja * (-b))
                    y2 = int(y0 - lavistaja * a)
                    
                    # Karsitaan muut kuin liki vaakasuorat
                    if x1 == x2:
                        m = 1000
                    else:
                        m = (y2 - y1)/(x2 - x1)
                    if abs(m) < 0.2: 
                        d = calc_dist_p_line(x1, y1, x2, y2, c[0], c[1]) - c[2]
                        d /= calib_data["ppmm"]
                        s_info.append({"rho": rho, "d":d, "y_mean": (y1 + y2)/2})

                        cv2.line(img, (x1, y1), (x2, y2), (0, 255, 0), line_width)

            # Etsitään mahdolliset duplikaattisuorat, poistetaan ne ja lasketaan
            # suorien lopulliset etäisyydet suoran ja sen duplikaattien etäisyyksien
            # keskiarvona.
            if suorat is not None and len(s_info) > 0:
                final_lines = [] # Lopulliset suorat
                skip_inds = [] # Kaikkien löydettyjen duplikaattien indeksit (-> skipataan)
                for i, s1 in enumerate(s_info):
                    if i not in skip_inds:
                        duplicate_inds = []
                        for j, s2 in enumerate(s_info[i+1:]):
                            if abs(s2["rho"] - s1["rho"]) < 30 * img.shape[1]/1600:
                                duplicate_inds.append(i + j + 1)
                        d_final = s1["d"]
                        for k in duplicate_inds:
                            d_final += s_info[k]["d"]
                        d_final /= len(duplicate_inds) + 1
                        final_lines.append({"d": d_final, "y_mean": s1["y_mean"]})
                        skip_inds += duplicate_inds
                
                # Kirjataan etäisyydet kuvaan
                for f in final_lines:
                    d = f["d"]
                    cv2.putText(img, f"et.: {d:.2f} mm", (cints[0] - 50, int((cints[1] + f["y_mean"])/2)), 
                    cv2.FONT_HERSHEY_SIMPLEX, font_face, (0, 255, 0), line_width)
                
                # Jos lopullisia suoria 1 tai 2 (eli ei ylimääräisiä)
                if len(final_lines) < 3:
                    # Järjestetään ylhäältä alas
                    final_lines=sorted(final_lines, key=lambda x: x["y_mean"])
                    dists1.append(final_lines[0]["d"])
                    if len(final_lines) == 2:
                        dists2.append(final_lines[1]["d"])
                    else:
                        dists2.append(None)

                # Jos ylimääräisiä suoria jäi, etäisyyksiä ei voi laskea 
                else:
                    dists1.append(None)
                    dists2.append(None)
            else:        
                dists1.append(None)
                dists2.append(None)
            
            if show_imgs:
                if img.shape[1] > 1200:
                    sc = 1200/img.shape[1]
                    img = cv2.resize(img, None, fx=sc, fy=sc)
                cv2.imshow("valmis", img)
                cv2.waitKey(0)

            # Jos tuloskansio on annettu, talletaan tuloskuvat
            # alkuperäisten kuvien nimillä.
            if res_folder is not None:
                current_subf = Path(folder).parts[-1]
                write_folder = folder.replace(current_subf, res_folder)
                write_folder = join(write_folder, current_subf)
                if not exists(write_folder):
                    makedirs(write_folder)
                write_name = join(write_folder,filename)
                cv2.imwrite(write_name, img)

    # Listat kuvakohtaisista etäisyyksistä numpy-taulukoiksi
    arr_dists1 = np.array(dists1)
    arr_dists2 = np.array(dists2)

    # Keskiarvot ja keskihajonnat (jos vähintään 1 mittaus onnistui)
    if any(dists1):
        dists1.append(np.mean(arr_dists1[arr_dists1 != None]))
        dists1.append(np.std(arr_dists1[arr_dists1 != None]))
    else:
        dists1 += [None, None]
    if any(dists2):
        dists2.append(np.mean(arr_dists2[arr_dists2 != None]))
        dists2.append(np.std(arr_dists2[arr_dists2 != None]))
    else:
        dists2 += [None, None]
    diams.append(np.mean(np.array(diams)))
    diams.append(np.std(np.array(diams)))
    filelist += ["ka", "khaj"]

    # Valmis dataframe, jossa sarakkeiden otsikot määritetty stringeinä ja 
    # itse sarakkeet numpy-taulukkona
    d = {"kuva": filelist, "et. 1": dists1, "et. 2": dists2, "sis.halk.": diams}
    df = DataFrame(data=d)

    return df

if __name__=="__main__":
    from pathlib import Path
    from kalibrointi import read_cal_file

    folder = "drive:/path/to/images"
    subf = Path(folder).parts[-1]
    calib_filename = join(folder.removesuffix(subf), "kalibraatio.json")
    calib_data = read_cal_file(calib_filename)

    df = process_image_folder(folder, calib_data, show_imgs=True)
    print(df)