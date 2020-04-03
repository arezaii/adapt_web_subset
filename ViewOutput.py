import os
import glob
from yattag import Doc, indent
import cgitb
import cgi


DOCUMENT_ROOT='/var/www/subset'


def make_sorry(doc, tag, text, line, guid):
    doc.asis('<!DOCTYPE html>')
    with tag('html'):
        with tag('body'):
            with tag('h1'):
                text('Sorry, the data for %s was not found on the server!' %guid)
    return indent(doc.getvalue())


def make_page(doc, tag, text, line, pngs, download_path):
    doc.asis('<!DOCTYPE html>')
    with tag('html'):
        with tag('body'):
            with tag('h1'):
                text('Hydrographs')

            with tag('div', id='download-container'):
                with tag('form', method='get', action=os.path.relpath(download_path, start=DOCUMENT_ROOT)):
                    with tag('button', type='submit'):
                        text('Download this data')

            with tag('div', id='photo-container'):
                # write each png
                for png in pngs:
                    doc.stag('img', src=os.path.relpath(png, start=DOCUMENT_ROOT), klass="photo")

    return indent(doc.getvalue())


def find_data(guid):
    id_path = os.path.join(DOCUMENT_ROOT, 'out', guid)
    data = glob.glob(id_path)
    if len(data) == 1:
        return id_path
    else:
        return None


def main():
    #args = parse_args(list(url))
    #pngs = get_pngs(args.png_dir)
    print("Content-type: text/html\r\n\r\n")
    cgitb.enable()
    doc, tag, text, line = Doc().ttl()
    form = cgi.FieldStorage()
    guid = form.getfirst('id', '')
    # try to find the id on the server
    id_loc = find_data(guid)
    # if id is not found, just say sorry
    if id_loc is None:
        html = make_sorry(doc,tag, text, line, guid)
    else:
    # if is found, show the hydrographs and download button
        html = make_page(doc, tag, text, line, glob.glob(os.path.join(DOCUMENT_ROOT,'out',guid,'png','*.png'), os.path.join(DOCUMENT_ROOT,'out',guid,'%s.tar.gz'%guid)))
    print(html)


if __name__ == '__main__':
    main()
