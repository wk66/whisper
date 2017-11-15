#!/usr/bin/env python

import optparse
import os
import sys
import time

import whisper

whisper_fill = __import__('whisper-fill')


class FileError(IOError): pass


def abort(text, status):
  print('ERROR: ' + text)
  sys.exit(status)


def warn(text):
  print('WARN: ' + text)


def check_args():
  option_parser = optparse.OptionParser(
    usage='%prog FILES-LIST SRC DST',
    description='copies data (if missing) from whisper files in SRC dir'
                ' to files in DST dir. FILES_LIST: must contain relative'
                ' filenames, relative to SRC and DST')
  (options, args) = option_parser.parse_args()
  if len(args) != 3:
    option_parser.print_help()
    abort('not 3 arguments', 1)
  files_list = args[0]
  if not os.path.isfile(files_list):
    abort('not a file: %s' % (files_list,), 1)
  src_dir = args[1]
  if not os.path.isdir(src_dir):
    abort('not a dir: %s' % (src_dir,), 1)
  dst_dir = args[2]
  if not os.path.isdir(dst_dir):
    abort('not a dir: %s' % (dst_dir,), 1)
  print('Running whisper-fill for relative filenames taken from: %s\n'
        'source files in: %s\n'
        'destination files in: %s' % (files_list, src_dir, dst_dir))
  return files_list, src_dir, dst_dir


def get_full_info(wsp):
  header = whisper.info(wsp)
  archives = header['archives']
  archives = sorted(archives, key=lambda t: t['retention'])
  now = time.time()
  for archive in archives:
    fromTime = now - archive['retention']
    (timeInfo, values) = whisper.fetch(wsp, fromTime, now)
    non_zero = [v for v in values if v > 0.0]
    yield len(non_zero)


def main():
  files_list, src_dir, dst_dir = check_args()
  if whisper.CAN_LOCK:
    whisper.LOCK = True
  with open(files_list) as filenames:
    for rel_filename in filenames:
      rel_filename = rel_filename.strip()
      if not rel_filename:
        continue
      try:
        src_filename = check_abs_filename(rel_filename, src_dir)
        dst_filename = check_abs_filename(rel_filename, dst_dir)
      except FileError:
        warn('file not found: "%s" in "%s"' % (rel_filename, src_dir))
      else:
        print 'filling: "%s"... ' % (rel_filename,),
        print 'src: %s' % str(list(get_full_info(src_filename)))
        print 'dst before: %s' % str(list(get_full_info(dst_filename)))
        whisper_fill.fill_archives(src_filename, dst_filename, time.time())
        print 'dst after: %s' % str(list(get_full_info(dst_filename)))


def check_abs_filename(rel_filename, src_dir):
  abs_filename = os.path.join(src_dir, rel_filename)
  if not os.path.isfile(abs_filename):
    raise FileError
  return abs_filename


if __name__ == "__main__":
  main()
