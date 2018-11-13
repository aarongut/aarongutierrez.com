#!/usr/bin/env python3

import argparse
import os
import sys

import boto3

BUCKET='www.aarongutierrez.com'
AWS_ACCESS_KEY='AKIAIDTVRR2EKQ5FYIEQ'
AWS_SECRET_KEY='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'

s3 = boto3.client('s3',
                  aws_access_key_id=AWS_ACCESS_KEY,
                  aws_secret_access_key=AWS_SECRET_KEY)

bench_fmt = """<a href="/img/bench/{0:03d}.jpg"><picture><source type="image/webp" srcset="/img/bench/{0:03d}.thumb.webp, /img/bench/{0:03d}.thumb@2x.webp 2x"><img src="/img/bench/{0:03d}.thumb.jpg"></picture></a>""" + "\n"

TYPE_MAP = {
    'asc': 'text/plain',
    'css': 'text/css',
    'gif': 'image/gif',
    'html': 'text/html; charset=utf8',
    'jpg': 'image/jpeg',
    'png': 'image/png',
    'webp': 'image/webp',
}

def upload_file(filename, overwrite=True):
    print('Uploading {} to {}/{}'.format(filename, BUCKET, filename))
    ext = filename.split('.')[-1]

    if not overwrite:
        try:
            existing = s3.get_object(Bucket=BUCKET, Key=filename)
            print('\tSkipping existing key ', filename)
            return
        except:
            pass

    s3.upload_file(filename, BUCKET, filename, ExtraArgs={
        'ACL': 'public-read',
        'ContentType': TYPE_MAP[ext]
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

def make_bench():
    imgs = os.listdir('img/bench')
    img_files = [f for f in filter_filenames(imgs, ['jpg', 'webp'])]
    num_imgs = int(len(img_files) / 4)

    with open('bench_template.html', 'r') as f:
        template = f.read()

    for i in range(1, num_imgs+1, 16):
        page = ''
        for j in range(i, min(num_imgs+1, i+16)):
            page += bench_fmt.format(j)

        prev_pg = i//16
        next_pg = i//16 + 2

        prev_link = '#' if (prev_pg == 0) else '/bench/{}.html'.format(prev_pg)
        next_link = '#' if (i+16 > num_imgs) else '/bench/{}.html'.format(next_pg)

        with open('bench/{}.html'.format(i//16 + 1), 'w') as out:
            out.write(template.format(page, prev_link, next_link))

def upload_bench():
    imgs = os.listdir('img/bench')
    img_files = [f for f in filter_filenames(imgs, ['jpg', 'webp'])]
    files = filter_filenames(os.listdir('bench'), 'html')
    for f in files:
        upload_file('bench/{}'.format(f))

    for f in img_files:
        upload_file('img/bench/{}'.format(f), overwrite=False)

def upload_img():
    files = filter_filenames(os.listdir('img'), ['jpg', 'webp'])
    for f in files:
        upload_file('img/{}'.format(f))

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
    pub_choices = ['all', 'root', 'img', 'bench-local', 'bench', '15418', 'campaign']
    parser.add_argument('pub', choices=pub_choices, help=pub_help)

    args = parser.parse_args()

    if args.pub == 'root' or args.pub == 'all':
        upload_root()
    if args.pub == 'img' or args.pub == 'all':
        upload_img()
    if args.pub == 'bench-local' or args.pub == 'all':
        make_bench()
    if args.pub == 'bench' or args.pub == 'all':
        upload_bench()
    if args.pub == '15418' or args.pub == 'all':
        upload_15418()
    if args.pub == 'campaign' or args.pub == 'all':
        upload_campaign()
