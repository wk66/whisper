#!/usr/bin/env python

import json
import optparse
import os
import signal
import sys

try:
  import whisper
except ImportError:
  raise SystemExit('[ERROR] Please make sure whisper is installed properly')

# Ignore SIGPIPE
try:
  signal.signal(signal.SIGPIPE, signal.SIG_DFL)
except AttributeError:
  # OS=windows
  pass


def main(sysv_args):
  option_parser = optparse.OptionParser(usage='''%prog [option] path [field]''')
  option_parser.add_option('--json', default=False, action='store_true',
                           help="Output results in JSON form")
  option_parser.add_option('--short', default=False, action='store_true',
                           help="Output results in short form as in storage-schemas.conf")
  (options, args) = option_parser.parse_args(sysv_args)

  if len(args) < 1:
    option_parser.print_help()
    sys.exit(1)

  path = args[0]
  if len(args) > 1:
    field = args[1]
  else:
    field = None

  try:
    info = whisper.info(path)
  except whisper.WhisperException as exc:
    raise SystemExit('[ERROR] %s' % str(exc))

  if field:
    print_field(field, path, info)
  elif options.json:
    print_json(info)
  elif options.short:
    print_short(info)
  else:
    print_default(info)


def print_field(field, path, info):
  info['fileSize'] = os.stat(path).st_size
  if field not in info:
    print('Unknown field "%s". Valid fields are %s' % (field, ','.join(info)))
    sys.exit(1)
  print(info[field])


def print_json(info):
  print(json.dumps(info, indent=2, separators=(',', ': ')))


def to_time_unit(seconds):
  if seconds % 60 != 0:
    return seconds, 's'
  minutes = seconds / 60
  if minutes % 60 != 0:
    return minutes, 'm'
  hours = minutes / 60
  if hours % 24 != 0:
    return hours, 'h'
  days = hours / 24
  if days % 365 != 0:
    return days, 'd'
  years = days / 365
  return years, 'y'


def print_short(info):
  archives = info.pop('archives')
  short_info_string = ''
  for _, archive in enumerate(archives):
    sec_pp_value, sec_pp_unit = to_time_unit(archive['secondsPerPoint'])
    retention_value, retention_unit = to_time_unit(archive['retention'])
    short_info_string += '%d%s:%d%s ' % (
      sec_pp_value, sec_pp_unit, retention_value, retention_unit)
  print(short_info_string)


def print_default(info):
  archives = info.pop('archives')
  for key, value in info.items():
    print('%s: %s' % (key, value))
  print('')
  for i, archive in enumerate(archives):
    print('Archive %d' % i)
    for key, value in archive.items():
      print('%s: %s' % (key, value))
    print('')


if __name__ == '__main__':
  main(sys.argv[1:])
