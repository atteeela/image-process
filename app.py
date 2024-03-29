#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Image Processing Service
A wrapper around GM commands for now
"""
import os
import requests
from PIL import ImageFont, Image, ImageDraw
from sh import gm
import stackhut

class ImageProc(stackhut.Service):
    def __init__(self):
        self.res_dir = os.path.join(stackhut.root_dir, 'res')

    def get_res(self, name):
        return os.path.join(self.res_dir, name)

    def _run_gm_command(self, cmd_list, in_url, new_ext=None):
        # get input file
        in_file = stackhut.download_file(in_url)
        out_file = "out_{}".format(in_file)

        if new_ext is not None:
            out_file = "{}.{}".format(os.path.splitext(out_file)[0], new_ext)

        # run GM command
        gm(cmd_list + [in_file, out_file])
        # save back to S3
        # out_url = upload_file(out_file, self.task_id, self.bucket)
        return stackhut.put_file(out_file)

    def blur(self, amount, url):
        return self._run_gm_command(['convert', '-blur', str(amount)], url)

    def resize(self, scale, url):
        return self._run_gm_command(['convert', '-resize', '{}%'.format(scale*100)], url)

    def rotate(self, angle, url):
        return self._run_gm_command(['convert', '-rotate', str(angle)], url)

    def convert(self, fileExt, url):
        return self._run_gm_command(['convert'], url, fileExt)

    def memeGenerate(self, topText, bottomText, url):
        """taken and adapted from ..."""
        top_text = topText.upper()
        bottom_text = bottomText.upper()

        in_file = stackhut.download_file(url)
        out_file = "out_{}".format(in_file)

        img = Image.open(in_file)
        image_size = img.size

        # find biggest font size that works
        font_size = int(image_size[1]/5)
        font = ImageFont.truetype(self.get_res("Impact.ttf"), font_size)
        top_text_size = font.getsize(top_text)
        bottom_text_size = font.getsize(bottom_text)
        while top_text_size[0] > image_size[0]-20 or bottom_text_size[0] > image_size[0]-20:
            font_size -= 1
            font = ImageFont.truetype(self.get_res("Impact.ttf"), font_size)
            top_text_size = font.getsize(top_text)
            bottom_text_size = font.getsize(bottom_text)

        # find top centered position for top text
        top_text_x = (image_size[0]/2) - (top_text_size[0]/2)
        top_text_y = 0
        top_text_pos = (top_text_x, top_text_y)

        # find bottom centered position for bottom text
        bottom_text_x = (image_size[0]/2) - (bottom_text_size[0]/2)
        bottom_text_y = image_size[1] - bottom_text_size[1]
        bottom_text_pos = (bottom_text_x, bottom_text_y)

        draw = ImageDraw.Draw(img)

        # draw outlines, there may be a better way
        outline_range = int(font_size/15)
        for x in range(-outline_range, outline_range+1):
            for y in range(-outline_range, outline_range+1):
                draw.text((top_text_pos[0]+x, top_text_pos[1]+y), top_text, (0,0,0), font=font)
                draw.text((bottom_text_pos[0]+x, bottom_text_pos[1]+y), bottom_text, (0,0,0), font=font)

        draw.text(top_text_pos, top_text, (255,255,255), font=font)
        draw.text(bottom_text_pos, bottom_text, (255,255,255), font=font)

        # save final image
        img.save(out_file)
        # out_url = upload_file(out_file, self.task_id, self.bucket)
        return stackhut.put_file(out_file)

SERVICES = {"Default" : ImageProc()}

