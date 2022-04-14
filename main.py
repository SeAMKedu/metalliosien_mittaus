from tkinter import filedialog as fd
from pandas import DataFrame, ExcelWriter
from numpy import array
from openpyxl import load_workbook
from glob import glob
from os.path import join
from pathlib import Path
from kalibrointi import read_cal_file
from mittaus import process_image_folder

# Kysytään kuvakansion ja kalibraatiotiedoston polut
main_folder = fd.askdirectory(title="Anna kuvakansio")
calib_filename = fd.askopenfilename(title="Anna kalibraatiotiedosto", 
                    filetypes=[("json-tiedostot", ".json")])

if main_folder == "" or calib_filename == "":
    print("Käyttäjä painoi cancelia. Ohjelmaa ei suoriteta.")
else:
    calib_data = read_cal_file(calib_filename) # Luetaan kalibraatiotiedosto
    subf_list = glob(main_folder + "/*/") # Alikansiorakenne
    result_folder_name = "results"  # Tuloskuvien kansion nimi
    result_file = join(main_folder, "results.xlsx") # Tulos-Excelin nimi

    # Listat mittausten keskiarvoista ja keskihajonnoista
    et1_kat = []
    et1_kht = []
    et2_kat = []
    et2_kht = []
    sis_kat = []
    sis_kht = []
    folder_names = []

    # Käsitellään pääkansion alikansiot yksi kerrallaan
    for i, subf in enumerate(subf_list):
        subf_name = Path(subf).parts[-1]
        if subf_name != result_folder_name and not "kal" in subf_name:
            df = process_image_folder(subf, calib_data, res_folder=result_folder_name)
            
            # Keskiarvot ja keskihajonnat talteen omiin listoihinsa
            et1_kat.append(df.iloc[-2]["et. 1"])
            et1_kht.append(df.iloc[-1]["et. 1"])
            et2_kat.append(df.iloc[-2]["et. 2"])
            et2_kht.append(df.iloc[-1]["et. 2"])
            sis_kat.append(df.iloc[-2]["sis.halk."])
            sis_kht.append(df.iloc[-1]["sis.halk."])
            folder_names.append(subf_name)

            if i == 0:
                # Eka kierros: Excel-tiedoston teko ja sen avaaminen,
                # jotta saadaan määriteltyä tiedosto ja sen välilehdet.
                df.to_excel(result_file, subf_name)
                book = load_workbook(result_file)
                writer = ExcelWriter(result_file, engine='openpyxl') 
                writer.book = book
                writer.sheets = dict((ws.title, ws) for ws in book.worksheets)
            else:
                # Muut kierrokset: lisätään välilehtiä
                df.to_excel(writer, subf_name)
                writer.save()
            
            # Lopuksi luodaan vielä yhteenvetovälilehti, jonne 
            # kirjataan mittausten keskiarvot ja keskihajonnat per 
            # kuvakansio.
            d = {"kansio": folder_names, 
                "et. 1 ka": array(et1_kat), 
                "et. 1 khaj.": array(et1_kht),
                "et. 2 ka": array(et2_kat), 
                "et. 2 khaj.": array(et2_kht), 
                "sis.halk. ka": array(sis_kat),
                "sis.halk. khaj.": array(sis_kht)}
            df = DataFrame(data=d)
            df.to_excel(writer, "yht.veto")
            writer.save()
