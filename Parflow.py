#!/var/www/cgi-bin/.envs/bin/python

# -*- coding: UTF-8 -*-# enable debugging
import os
import argparse
import glob
import sys
from yattag import Doc, indent
from urllib.parse import urlparse, urlunparse
import re
import cgitb
import cgi
import requests
import tarfile
import subprocess


def is_valid_url(arg):
    url = urlparse(arg)
    if not url.scheme == 'http':
        raise Exception("The url %s does not use http" % arg)
    if not url.netloc == 'subset.cuahsi.org':
        raise Exception("The url %s is not a cuahsi subset" % arg)
    if url.path.endswith(".tar.gz") and url.path.startswith("/data/"):    
        doc = re.split('/|\.', url.path.lstrip('/'))
        if len(doc) == 4 and len(doc[1]) == 40 and doc[1].isalnum():
            return url
    raise Exception("The url %s is not valid" % arg)


# def parse_args(args):
#     parser = argparse.ArgumentParser('Download a subset, run it, and process the output')

#     parser.add_argument("--url", "-u", dest="subset_url", required=True,
#                         help="the subset download path",
#                         type=lambda x: is_valid_url(x))

#     return parser.parse_args(args)


def make_page(doc, tag, text, line, url):
    doc.asis('<!DOCTYPE html>')
    with tag('html'):
        with tag('body'):
            with tag('h1'):
                text('Downloading data from %s' % urlunparse(url))

    return indent(doc.getvalue())


def make_data_dir(guid):
    path='/var/www/subset/data/%s' %guid
    if not os.path.isdir(path):
        os.mkdir(path)
    return path

def make_out_dir(guid):
    path='/var/www/subset/out/%s' %guid
    if not os.path.isdir(path):
        os.mkdir(path)
    return path

def download_file(url, out_dir, filename):
    responses = []
    if os.path.isfile(os.path.join(out_dir, filename)):
        print('file already downloaded, skipping')
        return
    try:
        # submit the request using the session
        response = requests.get(url, stream=True)
        responses.append(response)

        # raise an exception in case of http errors
        response.raise_for_status()

        # save the file
        with open(os.path.join(out_dir, filename), 'wb') as fd:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                fd.write(chunk)

    except requests.exceptions.HTTPError as e:
        # handle any errors here
        print(e)


def extract_archive(archive, destination):
    tar = tarfile.open(archive, 'r:gz')
    tar.extractall(path=destination)
    tar.close()

def run_model(guid):    
    cmd = "singularity run /var/www/subset/utils/parflow.sif simulation.tcl"
    
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, creationflags=0x08000000)
    process.wait()

def main():        
    #args = parse_args(list(url))
    #pngs = get_pngs(args.png_dir)
    print("Content-type: text/html\r\n\r\n")
    cgitb.enable()
    form = cgi.FieldStorage()
    url = is_valid_url(form.getfirst('url',''))
    guid = url.path.split('.')[0].lstrip('/').split('/')[1]
    data_path = make_data_dir(guid)
    out_path = make_out_dir(guid)
    #print("downloading data from: %s"%urlunparse(url))
    download_file(urlunparse(url), data_path, "%s.tar.gz"%guid)
    extract_archive(os.path.join(data_path,"%s.tar.gz"%guid), out_path)
    doc, tag, text, line = Doc().ttl()
    html = make_page(doc, tag, text, line, url)
    print(html)


if __name__ == '__main__':
    main()
