#!/usr/bin/env python3

# ------------------------------------------------------------------------------
# InternetSpeedLogger
#
# A Python script that continuously monitors and logs your internet speed. It
# tests both download and upload speeds at regular intervals and records the
# data in a CSV file for easy analysis and tracking. Ideal for auditing your
# network performance or ISP reliability over time.
#
# https://github.com/Andreas-Menzel/InternetSpeedLogger/
# https://pypi.org/project/InternetSpeedLogger/
# ------------------------------------------------------------------------------
# @author: Andreas Menzel
# @license: MIT License
# ------------------------------------------------------------------------------

import argparse
import csv
from datetime import datetime
from pathlib import Path
from signal import signal, SIGINT
from speedtest import Speedtest
from tempfile import gettempdir
from time import sleep


script_version = '1.3.0'


def argparse_check_positive(value):
    ivalue = int(value)
    if ivalue <= 0:
        raise argparse.ArgumentTypeError(
            "%s is an invalid positive int value" % value)
    return ivalue


def setupArgumentParser():
    parser = argparse.ArgumentParser(
        prog='InternetSpeedLogger',
        description="""
A Python script that continuously monitors and logs your internet
speed. It tests both download and upload speeds at regular intervals
and records the data in a CSV file for easy analysis and tracking.
Ideal for auditing your network performance or ISP reliability over
time.
            """,
        epilog="""
Default location of the log-file:
    A .csv-file will be created, which will contain all logged information.
    Default Filename: "YYYY-MM-DD_HH:MM:SS_internet_speeds.csv"
    Default Location: <tmp_dir>/InternetSpeedLogger/
        <tmp_dir> on Windows: C:\\TEMP, C:\\TMP, \\TEMP, or \\TMP, in that order
        <tmp_dir> on all other: /tmp, /var/tmp, or /usr/tmp, in that order
            """,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + script_version)
    parser.add_argument('-i', '--interval',
                        help='Testing interval in seconds. Make sure that the interval is not shorter than the time needed for testing. (default: %(default)s)',
                        type=argparse_check_positive,
                        default=60)
    parser.add_argument('-d', '--duration',
                        help='Duration of the entire test runs. The script will automatically end after this duration. Set to <= 0 for infinite. (default: %(default)s)',
                        type=int,
                        default=0)
    parser.add_argument('-l', '--log_file',
                        help='Filename for the log-file. NOTE: A similar filename will be chosen if a file with this name already exists.',
                        default='')
    parser.add_argument('-no', '--no_overwrite',
                        help='Set this flag to automatically select a similar log-filename, so a potentially already existing file will not be overwritten.',
                        action='store_true')
    return parser.parse_args()


def main():
    args = setupArgumentParser()

    st = Speedtest()

    datetimeString = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
    if args.log_file != '':
        if len(args.log_file) > 4 and args.log_file[-4:] == '.csv':
            csv_file = Path(f'{args.log_file}')
        else:
            csv_file = Path(f'{args.log_file}.csv')
    else:
        # Set to default/fallback location.
        csv_file = Path(
            f'{Path(gettempdir(), "InternetSpeedLogger", datetimeString)}_internet_speeds.csv')

    # Make sure that the log-file is unique and does not exist yet.
    if args.no_overwrite or args.log_file == '':
        if csv_file.exists():
            csv_file = Path(csv_file.parent,
                            f'{csv_file.stem}_{datetimeString}{csv_file.suffix}')
        if csv_file.exists():
            counter = 2
            new_csv_file = csv_file
            while new_csv_file.exists():
                new_csv_file = Path(
                    csv_file.parent, f'{csv_file.stem}_{counter}{csv_file.suffix}')
                counter = counter + 1
            csv_file = new_csv_file

    print(f"""\
InternetSpeedLogger (version {script_version})

Testing interval: {args.interval} s
Testing duration: {str(args.duration) + ' s' if args.duration > 0 else 'infinite'}
Log-file: "{csv_file.absolute()}"\
    """)

    csv_file.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_file, mode='w') as file:
        writer = csv.writer(file)
        writer.writerow(['Timestamp', 'Download (bps)', 'Upload (bps)',
                        'Datetime', 'Download (Mbps)', 'Upload (Mbps)'])
        file.flush()

    start_time = datetime.now().timestamp()
    while True:
        testing_time = datetime.now()
        testing_timestamp = testing_time.timestamp()

        print(f'\nTesting at {testing_time.strftime("%Y-%m-%d %H:%M:%S")}')
        print(f'\tDownload: ', end='')
        download = st.download()
        print(f'{round(download / 1000000)} Mbps')
        print(f'\tUpload: ', end='')
        upload = st.upload()
        print(f'{round(upload / 1000000)} Mbps')

        with open(csv_file, mode='a') as file:
            writer = csv.writer(file)
            writer.writerow([
                testing_timestamp,
                download,
                upload,

                testing_time.strftime("%Y-%m-%d %H:%M:%S"),
                round(download / 1000000),
                round(upload / 1000000)
            ])
            file.flush()

        if(args.duration > 0
                and testing_timestamp + args.interval > start_time + args.duration):
            break

        sleep(args.interval - (testing_timestamp - start_time)
              % args.interval)


def end(signal_received, frame):
    print('Goodbye!')
    exit(0)


if __name__ == "__main__":
    signal(SIGINT, end)
    main()
    end(None, None)
