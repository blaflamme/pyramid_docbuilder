# coding: utf-8
"""Pyramid Documentation Builder"""

from argparse import ArgumentParser
import logging
import os
import subprocess
import sys
from time import time

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE_DIR = 'src'
VENV_DIR = 'venv'
DOCS_DIR = 'docs'
OUTPUT_PATH = os.path.join('..', 'docs', 'projects')


def directory_exists(path):
    print 'verifying {0}'.format(path)
    if not os.path.isdir(path):
        print 'FAIL'
        return False
    print 'OK'
    return True

def create_directory(path):
    print 'creating {0}'.format(path)
    rcode = subprocess.call(['mkdir', '-p', path])
    if rcode > 0:
        print 'FAIL'
        return False
    print 'OK'
    return True

def create_venv(path):
    print 'creating virtualenv {0}'.format(path)
    rcode = subprocess.call(['virtualenv', '--no-site-packages', path])
    if rcode > 0:
        print 'FAIL'
        return False
    print 'OK'
    rcode = subprocess.call(['{0}/bin/easy_install'.format(path), 'sphinx'])
    if rcode > 0:
        print 'FAIL'
        return False
    print 'OK'
    rcode = subprocess.call(['{0}/bin/easy_install'.format(path),
                             'repoze.sphinx.autointerface'])
    if rcode > 0:
        print 'FAIL'
        return False
    print 'OK'
    return True

def remove_venv(path):
    print 'removing virtualenv {0}'.format(path)
    rcode = subprocess.call(['rm', '-Rf', path])
    if rcode > 0:
        print 'FAIL'
        return False
    print 'OK'
    return True

def build_doc(args, path, output, venv):
    print 'preparing repo'
    os.chdir(path)
    if os.path.exists('.git'):
        print 'print git detected'
        subprocess.call(['git', 'checkout', 'master'])
        subprocess.call(['git', 'pull'])
        subprocess.call(['git', 'checkout', args.tag])
    elif os.path.exists('.hg'):
        print 'hg detected'
        subprocess.call(['hg', 'checkout', 'tip'])
        subprocess.call(['hg', 'pull'])
        subprocess.call(['hg', 'update'])
        tag = args.tag if args.tag != 'master' else 'tip'
        subprocess.call(['hg', 'checkout', tag])

    print 'installing project and dependencies'
    subprocess.call(['{0}/bin/python'.format(venv), 'setup.py', 'develop'])
    os.chdir(args.docs)
    print 'building docs'
    subprocess.call(['rm', '-Rf', '_themes'])
    subprocess.call(['make', 'SPHINXBUILD={0}/bin/sphinx-build'.format(venv),
                     'clean', 'html'])

    print 'moving new doc to destination'
    subprocess.call('rm -Rf {0}/*'.format(output), shell=True)
    subprocess.call('cp -Rf {0}/_build/html/* {1}'.format(os.getcwd(), output),
                     shell=True)

    if os.path.exists('.git'):
        subprocess.call(['git', 'checkout', 'master'])
    elif os.path.exists('.hg'):
        subprocess.call(['hg', 'checkout', 'tip'])

def parse_args():
    p = ArgumentParser(description=__doc__)
    p.add_argument('-d', '--docs', default=DOCS_DIR,
                   help='Doc path in the package')
    p.add_argument('-o', '--output', default=OUTPUT_PATH,
                   help='Output directory to use')
    p.add_argument('-p', '--package', default=None, required=True,
                   help='Package to use')
    p.add_argument('-s', '--source', default=SOURCE_DIR,
                   help='Source directory to use')
    p.add_argument('-t', '--tag', default='master',
                   help='Tag to use')
    return p.parse_args()

def main():
    args = parse_args()

    if args.source:
        source = os.path.abspath(args.source)
        if not directory_exists(source):
            raise RuntimeError('choose another source directory')

    if args.output:
        output = os.path.join(args.output, args.package,
                              args.tag if args.tag != 'master' else 'dev')
        output = os.path.abspath(output)
        if not directory_exists(output):
            create_directory(output)

    if args.package:
        package = os.path.abspath(os.path.join(source, args.package))
        if not directory_exists(package):
            raise RuntimeError('unable to find package!')

    venv = os.path.abspath('-'.join([VENV_DIR, args.package, str(int(time()))]))
    create_venv(venv)
    build_doc(args, package, output, venv)
    remove_venv(venv)


if __name__ == '__main__':
    sys.exit(main())
