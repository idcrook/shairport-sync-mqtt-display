#!/usr/bin/env python3

# https://github.com/fengsp/color-thief-py

# pip install colorthief
# sudo apt install libtiff5

from colorthief import ColorThief

image1 = ColorThief("how_sweet.jpg")

# get the dominant color
dominant_color = image1.get_color(quality=1)
print('dominant_color (quality=1) = {}'.format(dominant_color))

dominant_color = image1.get_color()
print('dominant_color = {}'.format(dominant_color))

dominant_color = image1.get_color(quality=20)
print('dominant_color (quality=20) = {}'.format(dominant_color))

palette = image1.get_palette(color_count=3)
print('palette = {}'.format(palette))
