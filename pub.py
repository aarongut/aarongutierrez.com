#!/usr/bin/env python3

import argparse
import os
import sys
import subprocess
from functools import cache
from PIL import Image

import boto3

BUCKET='www.aarongutierrez.com'

session = boto3.Session(profile_name='push')
s3 = session.client('s3')


bench_fmt = """<a href="/bench/view/{0}"><picture><source type="image/webp" media="(min-width: 780px)" srcset="/img/bench/{0:03d}.1560.webp 2x, /img/bench/{0:03d}.780.webp"><source type="image/webp" srcset="/img/bench/{0:03d}.780.webp 2x, /img/bench/{0:03d}.390.webp"><source type="image/jpeg" media="(min-width: 780px)" srcset="/img/bench/{0:03d}.1560.jpg 2x, /img/bench/{0:03d}.780.jpg"><source type="image/jpeg" srcset="/img/bench/{0:03d}.780.jpg 2x, /img/bench/{0:03d}.390.jpg"><img src="/img/bench/{0:03d}.780.jpg" width="{1}px" height="{2}px"></picture></a>"""

bench_view_ftm = """<a href="/img/bench/{0:03d}.1560.jpg"><picture><source type="image/webp" media="(min-width: 780px)" srcset="/img/bench/{0:03d}.1560.webp 2x, /img/bench/{0:03d}.780.webp"><source type="image/webp" srcset="/img/bench/{0:03d}.780.webp 2x, /img/bench/{0:03d}.390.webp"><source type="image/jpeg" media="(min-width: 780px)" srcset="/img/bench/{0:03d}.1560.jpg 2x, /img/bench/{0:03d}.780.jpg"><source type="image/jpeg" srcset="/img/bench/{0:03d}.780.jpg 2x, /img/bench/{0:03d}.390.jpg"><img src="/img/bench/{0:03d}.780.jpg" width="{1}px" height="{2}px"></picture></a>"""

TYPE_MAP = {
    'asc': 'text/plain',
    'css': 'text/css',
    'gif': 'image/gif',
    'html': 'text/html; charset=utf8',
    'jpg': 'image/jpeg',
    'png': 'image/png',
    'webp': 'image/webp',
}

@cache
def current_keys():
    print('Fetching existing keys in {}'.format(BUCKET))
    existing = s3.list_objects_v2(Bucket=BUCKET)
    keys = set([content['Key'] for content in existing['Contents']])
    while existing['IsTruncated']:
        existing = s3.list_objects_v2(Bucket=BUCKET, ContinuationToken=existing['NextContinuationToken'])
        keys = keys.union(set([content['Key'] for content in existing['Contents']]))

    return keys


def upload_file(filename, overwrite=True):
    if not overwrite and filename in current_keys():
        print('Skipping existing key {}'.format(filename))
        return

    print('Uploading {} to {}/{}'.format(filename, BUCKET, filename))
    ext = filename.split('.')[-1]

    s3.upload_file(filename, BUCKET, filename, ExtraArgs={
        'ACL': 'public-read',
        'ContentType': TYPE_MAP[ext],
        'CacheControl': 'public, max-age={}'.format(31536000 if ext in ['gif', 'jpg', 'png', 'webp'] else 86400)
    })

    if (ext == 'html'):
        # Also upload the file without .html
        s3.upload_file(filename, BUCKET, filename[:-5], ExtraArgs={
            'ACL': 'public-read',
            'ContentType': TYPE_MAP[ext],
            'CacheControl': 'public, max-age={}'.format(31536000 if ext in ['gif', 'jpg', 'png', 'webp'] else 86400)
        })

    print('\tDone.')

def filter_filenames(filenames, ext):
    for f in filenames:
        if (isinstance(ext, (list,)) and (f.split('.')[-1] in ext) \
            or f.split('.')[-1] == ext):
            yield f

def upload_root():
    upload_file('index.html')
    upload_file('site.css')
    upload_file('pubkey.asc')


def thumbnail_bench(src):
    sizes = [1560, 780, 390]
    formats = ["webp", "jpg"]

    filename = src.split(".")[0]

    for size in [1560, 780, 390]:
        for image_type in ["webp", "jpg"]:
            output = "img/bench/{}.{}.{}".format(filename, size, image_type)
            if not os.path.exists(output):
                print("Thumbnailing {}...".format(output))
                subprocess.run(["convert", "img/bench/{}".format(src),
                                "-resize", "{}x".format(size),
                                "-quality", "40", output], check=True)
            else:
                print("Thumbnail {} exists".format(output))

def make_bench():
    imgs = os.listdir('img/bench')
    img_files = [f for f in filter_filenames(imgs, 'png')]

    for img in img_files:
        thumbnail_bench(img)

    num_imgs = int(len(img_files))

    with open('bench_template.html', 'r') as f:
        template = f.read()

    for i in range(1, num_imgs+1, 16):
        page = ''
        for j in range(i, min(num_imgs+1, i+16)):
            idx = num_imgs + 1 - j
            with Image.open('img/bench/{0:03d}.png'.format(idx)) as img:
                width,height = img.size
            page += bench_fmt.format(idx, width, height)

        prev_pg = i//16
        next_pg = i//16 + 2

        prev_link = '#' if (prev_pg == 0) else '/bench/{}'.format(prev_pg)
        next_link = '#' if (i+16 > num_imgs) else '/bench/{}'.format(next_pg)

        with open('bench/{}.html'.format(i//16 + 1), 'w') as out:
            out.write(template.format(page, prev_link, next_link))

    for i in range(1, num_imgs+1):
        make_bench_view(i,
                        '#' if (i-1 == 0) else str(i-1),
                        '#' if (i+1 > num_imgs) else str(i+1))


def make_bench_view(idx, prev, nxt):
    with open('bench_view_template.html', 'r') as f:
        template = f.read()

    with Image.open('img/bench/{0:03d}.png'.format(idx)) as img:
        width,height = img.size

    body = bench_view_ftm.format(idx, width, height)

    preview = "/img/bench/{0:03d}.780.jpg".format(idx)

    with open('bench/view/{}.html'.format(idx), 'w') as out:
        out.write(template.format(body, idx, preview,  prev, nxt))

def upload_bench():
    imgs = os.listdir('img/bench')
    img_files = [f for f in filter_filenames(imgs, ['jpg', 'webp'])]
    grid = filter_filenames(os.listdir('bench'), 'html')
    view = filter_filenames(os.listdir('bench/view'), 'html')

    for f in grid:
        upload_file('bench/{}'.format(f))

    for f in view:
        key = 'bench/view/{}'.format(f)
        upload_file('bench/view/{}'.format(f), overwrite=False)

    for f in img_files:
        key = 'img/bench/{}'.format(f)
        upload_file(key, overwrite=False)

def upload_img():
    files = filter_filenames(os.listdir('img'), ['jpg', 'webp'])
    for f in files:
        upload_file('img/{}'.format(f))

def upload_15411():
    upload_file('15411/index.html')

def upload_15418():
    upload_file('15418/index.html')
    upload_file('15418/style.css')

def upload_campaign():
    files = filter_filenames(os.listdir('campaign'),
                             ['html', 'css', 'jpg', 'png', 'gif'])
    for f in files:
        upload_file('campaign/{}'.format(f))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Publish www.aarongutierrez.com')

    pub_help = 'What to publish'
    pub_choices = [
        'all',
        'root',
        'img',
        'bench-local',
        'bench',
        '15411',
        '15418',
        'campaign',
    ]
    parser.add_argument('pub', choices=pub_choices, help=pub_help)

    args = parser.parse_args()

    if args.pub == 'root' or args.pub == 'all':
        upload_root()
    if args.pub == 'img' or args.pub == 'all':
        upload_img()
    if args.pub == 'bench-local' or args.pub == 'bench' or args.pub == 'all':
        make_bench()
    if args.pub == 'bench' or args.pub == 'all':
        upload_bench()
    if args.pub == '15411' or args.pub == 'all':
        upload_15411()
    if args.pub == '15418' or args.pub == 'all':
        upload_15418()
    if args.pub == 'campaign' or args.pub == 'all':
        upload_campaign()
