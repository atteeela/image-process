# Image Process
## An Image Manipulation Service

`image-process` is a StackHut service that performs various image manipulation tasks and can be used to generate memes. It's powered by

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

This example shows calling the service method `stackhut/image-process/Default.memeGenerate` using the Python client libraries to add a comment to an image and generate a meme.

```python
import stackhut_client as client
image_process = client.SHService('stackhut', 'image-process')
meme_url = image_process.Default.memeGenerate("I'm not saying it's containers...", "...but it's containers", "https://raw.githubusercontent.com/danieldiekmeier/memegenerator/master/aliens.jpg")
```

## Detailed Documentation

### Overview

This Python-based service demonstrates the following features,

* File manipulation
* OS and language dependencies
* Embedding resource files within a service

We also recommend looking at other, more detailed, examples of using StackHut to [convert PDF files](https://github.com/StackHut/pdf-tools) and [render webpages headless-ly](https://github.com/StackHut/web-tools).

The functions in this service operate by downloading an image referenced by a URL (e.g. one uploaded by a user), modifying the image using the open-source [GraphicsMagick](http://www.graphicsmagick.org/)) library amongst others, and uploading the result to a URL that is returned to the user.

To accomplish this we need to configure the service within the `Hutfile.yaml` to include the necessary OS/language libraries and to bundle resource files, and make use of the [StackHut runtime library](http://stackhut.readthedocs.org/en/latest/creating_service/service_runtime.html) within our `app.py` service code to handle files.


### API Definition (`api.idl`)

The API definition below defines the publicly accessible entry-points to the service that can be called from clients, e.g. client-side JS or mobile applications. Here we declare several functions that operate on images and return the result. 
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
}
```


### Service Configuration (`Hutfile.yaml`)

The `Hutfile.yaml` listed below follows the format described in the [documentation](http://stackhut.readthedocs.org/en/latest/creating_service/service_structure.html#hutfile): specifying the base OS (e.g. Fedora, Debian, etc.), the language stack (e.g. Python, NodeJS, etc.), and so on. 

Now let's look at the `os_deps` field, this is a list of OS packages that are to be installed and embedded within the image - packages one would install using `apt-get` or `yum` within a Linux distribution. 
Here we configure the service to include the `GraphicsMagick` and `python3-pillow` package from the Fedora package repository.

Finally let's look at the `files` field, this is a list of files within the project directory that you wish to package up within the service for deployment.
This list can be either individual files or directories, in which case the entire contests of the directory is included. (Note, you must explicitly list additional files within this field to ensure they exist during testing and deployment. By default only the basic project files are packaged up.)


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

This application code in [`app.py`](https://github.com/StackHut/image-process/blob/master/app.py) forms the service entry-points exposed by the `pdf-tools` service, with the methods and parameters matching those described above and in the `api.idl`.
This is standard [Python 3](http://www.python.org) code however there are a few important points to note around file handling and shelling out to external commands.

#### File Handling

We use the [StackHut runtime functions](http://stackhut.readthedocs.org/en/latest/creating_service/service_runtime.html) to aid file handling within the service - this includes the functions `stackhut.download_file()` and `stackhut.put_file()` that transparently download and upload files respectively to cloud storage. Files are processed within the current working directory, this is unique to each request and flushed upon request completion. Files themselves live on the cloud for approximately a few hours before being removed.

#### Running Commands

As mentioned previously, we indicating a dependency upon the `GraphicsMagick` Fedora package within our service. This package installs the `gm` binary that can be used within the service.

To process images with GraphicsMagick we need to be able to call the `gm` binary from within our service function. Generally this is done by using your language's process management features to execute the binary as a sub-process. 
When using Python we recommend and use the [sh](https://amoffat.github.com/sh) package that presents a simple way to call external binaries from within your service. 
However it's important to note that techniques exist in every language to call an binary embedded within the service - your service is running in a secure, custom container and you can do anything as needed inside it.


