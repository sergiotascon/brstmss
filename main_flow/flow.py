import cv2
import numpy as np
from candidates_detection.find_candidates import find_candidates
from false_positive_reduction.false_positive_reduction import border_false_positive_reduction
from evaluation.dice_similarity import extract_ROI
from feature_extraction.build_features_file import extract_features
from .split_features import create_entry, create_features_dataframe, drop_unwanted_features

COLOURS =\
    [(255, 0, 0),
     (0, 255, 0),
     (0, 0, 255),
     (255, 255, 0),
     (255, 0, 255),
     (0, 255, 255),
     (100, 255, 0),
     (255, 100, 0),
     (255, 100, 100)]

def __generate_outputs (img, rois, output):
    normalized_img = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
    normalized_img = cv2.cvtColor(normalized_img, cv2.COLOR_GRAY2BGR)
    for roi in rois:
        cv2.drawContours(normalized_img, roi.get('Contour'), -1, COLOURS[roi.get('Slice')], 2)

    cv2.imwrite(output, normalized_img)

def __process_scales(filename, img, all_scales):

    dataframe = []
    for slice_counter in np.arange(all_scales.shape[2]):
        slice = all_scales[:, :, slice_counter]

        if slice.max() <= 0:
            continue

        slice = 255 * slice
        _, contours, _ = cv2.findContours(slice, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
        for roi_counter in np.arange(len(contours)):
            roi, boundaries = extract_ROI(contours[roi_counter], img)
            bw_img = np.zeros_like(img)
            cv2.drawContours(bw_img, contours, roi_counter, 1, -1)
            roi_bw, _ = extract_ROI(contours[roi_counter], bw_img)

            [cnt_features, textures, hu_moments, lbp, tas_features] = \
                extract_features(roi, contours[roi_counter], roi_bw)
            entry = create_entry(
                filename, slice_counter, roi_counter, cnt_features, textures, hu_moments, lbp, tas_features, contours[roi_counter], slice_counter)
            dataframe.append(entry)

    return dataframe


def get_rois_from_image(path, filename):
    img = cv2.imread(path+filename, cv2.IMREAD_UNCHANGED)
    all_scales = find_candidates(img, 3, debug=False)
    all_scales = border_false_positive_reduction(all_scales, img)
    features = __process_scales(path + filename, img, all_scales)
    df_features = create_features_dataframe(features)
    df_features = drop_unwanted_features(df_features)
    df_features.to_csv(path + "out.csv")
    #Classification.
    __generate_outputs(img, features, path + "out.tif")