#!/usr/bin/env python3

# https://github.com/fengsp/color-thief-py

# pip install colorthief
# sudo apt install libtiff5

from colorthief import ColorThief

image1 = ColorThief("how_sweet.jpg")

# get the dominant color
dominant_color = image1.get_color(quality=1)
print("dominant_color (quality=1) = {}".format(dominant_color))

dominant_color = image1.get_color()
print("dominant_color = {}".format(dominant_color))

dominant_color = image1.get_color(quality=20)
print("dominant_color (quality=20) = {}".format(dominant_color))

palette = image1.get_palette(color_count=3)
print("palette = {}".format(palette))

image2 = ColorThief("joker.jpg")

# get the dominant color
dominant_color = image2.get_color(quality=1)
print("dominant_color (quality=1) = {}".format(dominant_color))

dominant_color = image2.get_color()
print("dominant_color = {}".format(dominant_color))

dominant_color = image2.get_color(quality=20)
print("dominant_color (quality=20) = {}".format(dominant_color))

palette = image2.get_palette(color_count=3)
print("palette = {}".format(palette))

image3 = ColorThief("dust.jpg")

# get the dominant color
dominant_color = image3.get_color(quality=1)
print("dominant_color (quality=1) = {}".format(dominant_color))

dominant_color = image3.get_color()
print("dominant_color = {}".format(dominant_color))

dominant_color = image3.get_color(quality=20)
print("dominant_color (quality=20) = {}".format(dominant_color))

palette = image3.get_palette(color_count=3)
print("palette = {}".format(palette))

# output on raspberry pi 3 running raspbian stretch
"""
dominant_color (quality=1) = (242, 241, 234)
dominant_color = (242, 242, 235)
dominant_color (quality=20) = (242, 241, 234)
palette = [(242, 241, 234), (83, 65, 58), (151, 99, 75), (182, 159, 117)]
dominant_color (quality=1) = (209, 212, 210)
dominant_color = (209, 212, 210)
dominant_color (quality=20) = (209, 212, 211)
palette = [(45, 35, 29), (209, 212, 210), (151, 170, 191), (121, 117, 154)]
dominant_color (quality=1) = (49, 77, 85)
dominant_color = (49, 76, 84)
dominant_color (quality=20) = (49, 77, 85)
palette = [(213, 200, 179), (49, 76, 84), (103, 81, 76), (153, 111, 81)]
"""
