import cv2
import json
import numpy as np

def read_cal_file(cal_filename):
    """Kalibraatiotiedoston lukeminen

    Args:
        cal_filename (string): Polku kalibraatiotiedoston

    Returns:
        dict: Kalibraatiodata sanakirjana
    """
    with open(cal_filename) as json_file:
        json_data = json.load(json_file)
        json_file.close()

    cal_data = {}
    cal_data["camera_matrix"] = np.asarray(json_data["camera_matrix"])
    cal_data["distortion_coeffs"] = np.asarray(json_data["distortion_coeffs"])
    cal_data["new_camera_matrix"] = np.asarray(json_data["new_camera_matrix"])
    cal_data["perspective_transformation"] = np.asarray(json_data["perspective_transformation"])
    cal_data["ppmm"] = json_data["ppmm"]

    return cal_data


def calibrate_image(img, cal_data):
    """Kuvan kalibrointifunktio

    Args:
        img (numpy-taulukko): Kuva
        cal_data (dict): Kalibrointidata sanakirjana

    Returns:
        numpy-taulukko: Korjattu kuva
    """

    # Korjataan linssi- ja perspektiivivääristymä
    img_ud = cv2.undistort(img, cal_data["camera_matrix"], 
                            cal_data["distortion_coeffs"], None, 
                            cal_data["new_camera_matrix"])
    img_ptrans = cv2.warpPerspective(img_ud, 
                                    cal_data["perspective_transformation"],
                                    (img.shape[1], img.shape[0]))
    return img_ptrans

