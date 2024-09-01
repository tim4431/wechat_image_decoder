#!/usr/bin/env python
# zhangxiaoyang.hit[at]gmail.com

import re
import os
import argparse
import logging
import sys

# # Set up logging
# logging.basicConfig(
#     filename='wechat_image_decoder.log',
#     filemode='a',
#     format='%(asctime)s - %(levelname)s - %(message)s',
#     level=logging.INFO
# )

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Create file handler for logging to file
file_handler = logging.FileHandler('wechat_image_decoder.log')
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# Create console handler for printing to console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

class WechatImageDecoder:
    def __init__(self, dat_file):
        dat_file = dat_file.lower()

        decoder = self._match_decoder(dat_file)
        decoder(dat_file)

    def _match_decoder(self, dat_file):
        decoders = {
            r'.+\.dat$': self._decode_pc_dat,
            r'cache\.data\.\d+$': self._decode_android_dat,
            None: self._decode_unknown_dat,
        }

        for k, v in decoders.items():
            if k is not None and re.match(k, dat_file):
                return v
        return decoders[None]

    def _decode_pc_dat(self, dat_file):

        def do_magic(header_code, buf):
            return header_code ^ list(buf)[0] if buf else 0x00

        def decode(magic, buf):
            return bytearray([b ^ magic for b in list(buf)])

        def guess_encoding(buf):
            headers = {
                'jpg': (0xff, 0xd8),
                'png': (0x89, 0x50),
                'gif': (0x47, 0x49),
            }
            for encoding in headers:
                header_code, check_code = headers[encoding]
                magic = do_magic(header_code, buf)
                _, code = decode(magic, buf[:2])
                if check_code == code:
                    return (encoding, magic)
            logging.error('Decode failed')
            sys.exit(1)

        with open(dat_file, 'rb') as f:
            buf = bytearray(f.read())
        file_type, magic = guess_encoding(buf)

        img_file = re.sub(r'.dat$', '.' + file_type, dat_file)
        with open(img_file, 'wb') as f:
            new_buf = decode(magic, buf)
            f.write(new_buf)

    def _decode_android_dat(self, dat_file):
        with open(dat_file, 'rb') as f:
            buf = f.read()

        last_index = 0
        for i, m in enumerate(re.finditer(b'\xff\xd8\xff\xe0\x00\x10\x4a\x46', buf)):
            if m.start() == 0:
                continue

            imgfile = '%s_%d.jpg' % (dat_file, i)
            with open(imgfile, 'wb') as f:
                f.write(buf[last_index: m.start()])
            last_index = m.start()

    def _decode_unknown_dat(self, dat_file):
        raise Exception('Unknown file type')


def process_single_file(file_path, delete_after_success=False)->int:
    if not os.path.isfile(file_path):
        logging.error(f"{file_path} is not a valid file.")
        return 0

    # check file extension is .dat, else skip
    if file_path.endswith('.dat'):
        try:
            WechatImageDecoder(file_path)
            logging.info(f"Decoded {file_path}")
            if delete_after_success:
                os.remove(file_path)
                logging.info(f"Deleted {file_path}")
            return 1
        except Exception as e:
            logging.error(f"Failed to decode {file_path}: {e}")
            return 0


def process_folder(folder_path, delete_after_success=False)->int:
    if not os.path.isdir(folder_path):
        logging.error(f"{folder_path} is not a valid directory.")
        return 0

    processed_file_num=0
    try:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                dat_file = os.path.join(root, file)
                n=process_single_file(dat_file, delete_after_success)
                processed_file_num+=n
    except Exception as e:
        logging.error(e)

    return processed_file_num


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Decode WeChat .dat files.', add_help=True)
    parser.add_argument('path', type=str, help='Specify the file or folder path.')
    parser.add_argument('-r', action='store_true', help='Recursively process files in the folder.')
    parser.add_argument('-d', action='store_true', help='Delete original .dat file after successful conversion.')

    args = parser.parse_args()

    if args.r:
        n=process_folder(args.path, delete_after_success=args.d)
    else:
        n=process_single_file(args.path, delete_after_success=args.d)
    #
    logger.info(f"Program exit with {n} files processed.")
