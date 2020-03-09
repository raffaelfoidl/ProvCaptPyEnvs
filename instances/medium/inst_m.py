import os

import numpy
import matplotlib.pyplot
import scipy.ndimage
import argparse

root, filename = os.path.split(__file__)
in_path = os.path.join(root, "in.jpg")


def parse_args():
    parser = argparse.ArgumentParser(description="Reads an image and applies an Gaussian blur filter to it. Afterwards,"
                                                 "the resulting image is compared to the original one and a diff "
                                                 "image is saved (white pixel means change black -> white or "
                                                 "white -> black; black pixel means no change in color)")
    parser.add_argument("sigma", metavar="sigma", type=int, help="sigma for the Gaussian blur")
    parser.add_argument("input", metavar="in", type=str, help="input file path")
    parser.add_argument("output", metavar="out", type=str, help="output file path")
    parser.add_argument("diff", metavar="diff", type=str, help="diff file path")
    return parser.parse_args()


def blur_image(img, sigma=3):
    # third axis holds color channels -> leave it untouched (otherwise averaging leads image to being near-grayscale)
    filtered_data = scipy.ndimage.filters.gaussian_filter(img, sigma=(sigma, sigma, 0))
    return filtered_data


def get_diff(img1, img2):
    """Gets the absolute difference of each and every pixel between the two parameters img1 and img2, whereby
    img1 denotes the image as it was given as input and img2 descirbes the one with a Gaussian blur applied to it"""
    if img1.shape != img2.shape:
        print("Error, images are not of same dimensions")
        exit(1)

    y_range = range(img1.shape[0])
    x_range = range(img1.shape[1])

    # create empty x * y array which will contain the diffs
    diff_per_pixel = [[0 for _ in x_range] for _ in y_range]
    last_percentage = 0
    for y in y_range:
        for x in x_range:
            px_1 = img1[y, x]
            px_2 = img2[y, x]
            diff = abs(px_1.astype(numpy.int16) - px_2.astype(numpy.int16))
            diff_per_pixel[y][x] = diff.sum()

        new_percentage = int(round((y / img1.shape[0]) * 100, -1))  # round to nearest ten
        if new_percentage != last_percentage and new_percentage != 100:
            last_percentage = new_percentage
            print("{} % done".format(new_percentage))

    return diff_per_pixel


def save_diff_image(path, diffs):
    if len(diffs) < 1:
        print("Error, diff does not contain rows")
        exit(1)

    matplotlib.pyplot.imsave(path, numpy.array(diffs), cmap="gray")


"""
@begin inst_m.main @desc Blurs an image and computes the differences to the original
@param sigma @desc sigma for gauss filter
@in in @as input_path @desc input file
@param out @as output_path @desc output image file path
@param diff @desc diff image file path
@out diff_file @uri file:{diff}
@out out_file @uri file:{out}
"""


def main():
    args = parse_args()

    if not os.path.exists(args.input):
        print("Could not find input file. Abort.")
        exit(1)

    """
    @begin read_input @desc read image from input path
    @in in @as input_path
    @out input_file
    """
    print("Reading input file...")
    in_file = matplotlib.pyplot.imread(args.input)
    print("Done.\n")
    """
    @end read_input
    """

    """
    @begin apply_gauss @desc apply gaussian blur with\nspecified parameter to input file
    @in input_file
    @in sigma
    @out blurred_image
    """
    print("Applying Gaussian blur to input file (sigma = {0})...".format(args.sigma))
    out_file = blur_image(in_file, args.sigma)
    print("Done.\n")
    """
    @end apply_gauss
    """

    """
    @begin save_out_file @desc persist blurred image
    @in blurred_image
    @in out @as output_path
    @return out_file @uri file:{out}
        @log Done saving output image
    """
    print("Saving output file...")
    matplotlib.pyplot.imsave(args.output, out_file)
    print("Done.\n")
    """
    @end save_out_file
    """

    """
    @begin calculate_differences @desc compute color\ndifferences in pixels
    @in input_file
    @in blurred_image
    @out diff_image
        @log {percentage} % done
        @log Done calculating
    """
    print("Calculating differences in pixel colors...")
    diff = get_diff(in_file, out_file)
    print("Done.\n")
    """
    @end calculate_differences
    """

    """
    @begin save_diff_image @desc persist image with\ncolor differences
    @in diff
    @in diff_image
    @out diff_file @uri file:{diff}
    """
    print("Saving diff image...")
    save_diff_image(args.diff, diff)
    """
    @end save_diff_image
    """
    print("Done.\n")


"""
@end inst_m.main
"""

if __name__ == "__main__":
    main()
