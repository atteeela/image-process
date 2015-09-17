# Image Process
# An Image Manipulation Service

## A PDF Processing Service

`image-process` is an image processing service that includes many basic and more advanced image manipulation functions. It's powered by

* [GraphicsMagick](http://www.graphicsmagick.org/)
* [Python Pillow](https://python-pillow.github.io/).
* Meme generation code derived from [https://github.com/danieldiekmeier/memegenerator].

## Usage

### Service Interface (`api.idl`)

#### `Default` Interface

* `convert(fileExt string, url string) string`
    convert image at URL

* `memeGenerate(topText string, bottomText string, url string) string`
    generate a "meme"-style subtitle to an image

* `rotate(angle float, url string) string`
    Rotate image at URL
    
* `resize(scale float, url string) string`
    Resize image at URL

* `blur(amount float, url string) string`
    Blur image at URL


### Example

This example shows calling the service method `stackhut/pdf-tools/Default.toImage` using the Python client libraries to convert an externally-hosted PDF to an image and upload the result.

```python
import stackhut_client as client
pdf_tools = client.SHService('stackhut', 'pdf-tools')
images_url = pdf_tools.Default.toImage("http://www.scala-lang.org/docu/files/ScalaTutorial.pdf", true)
```

## Detailed Documentation

### Overview

This Python-based service demonstrates the following features,

* File manipulation
* OS dependencies
* *Shelling*-out to binary/command-line tools from within a service

The functions in this service operate by downloading a PDF referenced by a URL (e.g. one uploaded by a user), modifying the PDF using the open-source [Poppler](http://poppler.freedesktop.org/) library, and uploading the result to a URL that is returned to the user.
To accomplish this we need to configure the service within the `Hutfile.yaml` to include the necessary OS libraries, and make use of the [StackHut runtime library](http://stackhut.readthedocs.org/en/latest/creating_service/service_runtime.html) within our `app.py` service code to handle files.


### API Definition (`api.idl`)

The API definition below defines the publicly accessible entry-points to the service that can be called from clients, e.g. client-side JS or mobile applications. Here we define two functions, `toImage` and `toText` that each convert a PDF file and return the result. 
The syntax is somewhat similar to defining an interface in Java but using basic JSON types - this is described further in the [StackHut documentation](http://stackhut.readthedocs.org/en/latest/creating_service/app_structure.html#interface-definition-api-idl).


```java
interface Default {
    // convert image at URL
    convert(fileExt string, url string) string

    // generate a "meme"-style subtitle to an image
    memeGenerate(topText string, bottomText string, url string) string

    // Rotate image at URL
    rotate(angle float, url string) string
    
    // Resize image at URL
    resize(scale float, url string) string

    // Blur image at URL
    blur(amount float, url string) string
}```


### Service Configuration (`Hutfile.yaml`)

The `Hutfile.yaml` listed below follows the format described in the [documentation](http://stackhut.readthedocs.org/en/latest/creating_service/service_structure.html#hutfile): specifying the base OS (e.g. Fedora, Debian, etc.), the language stack (e.g. Python, NodeJS, etc.), and so on. 

Now let's look at the `os_deps` field, this is a list of OS packages that are to be installed and embedded within the image - packages one would install using `apt-get` or `yum` within a Linux distribution. 
Here we configure the service to include the `poppler-utils` package from the Debian package repository, providing the command-line tools we require to process our incoming PDF files.

```yaml
# Service name (a combination of lower case letters, numbers, and dashes)
name: image-process

# Service description
description: Image Processing Service

# GitHub URL to the project
github_url: https://github.com/StackHut/image-process

# The service dependencies, in terms of the base OS and language runtime
baseos: fedora
stack: python

# any OS packages we require within the stack
os_deps:
    - GraphicsMagick
    - python3-pillow

# a list of files/dirs we wish to copy into the image
files: 
    - res

# Persist the service between requests
persistent: True

# Restrict service access to authenticated users
private: False
```

### Application Code (`app.py`) 

This application code below forms the service entry-points exposed by the `pdf-tools` service, with the methods and parameters matching those described above and in the `api.idl`.
This is standard [Python 3](http://www.python.org) code however there are a few important points to note around file handling and shelling out to external commands.


```python
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
```

#### File Handling

We use the [StackHut runtime functions](http://stackhut.readthedocs.org/en/latest/creating_service/service_runtime.html) to aid file handling within the service - this includes the functions `stackhut.download_file()` and `stackhut.put_file()` that transparently download and upload files respectively to cloud storage. Files are processed within the current working directory, this is unique to each request and flushed upon request completion. Files themselves live on the cloud for approximately a few hours before being removed.

#### Running Commands

As mentioned previously, we indicating a dependency upon the `poppler-utils` Debian package within our service. This package includes several binaries, such as `pdftocairo` and `pdftotext`, that can be used within the service.

To convert PDFs we need to be able to call these binaries from within our service function. Generally this is done by using your language's process management features to execute the binary as a sub-process. 
When using Python we recommend and use the [sh](https://amoffat.github.com/sh) package that presents a simple way to call external binaries from within your service. 
However it's important to note that techniques exist in every language to call an binary embedded within the service - your service is running in a secure, custom container and you can do anything as needed inside it.


