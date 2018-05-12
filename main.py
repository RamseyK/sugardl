import sys
import argparse
from sugardl import SugarDL


def main():
    parser = argparse.ArgumentParser(description="A tool to automate downloading all files from your SugarSync account")
    parser.add_argument('-u', '--user', type=str, required=True, help="SugarSync Username/Email")
    parser.add_argument('-p', '--password', type=str, required=True, help="Password")
    parser.add_argument('-a', '--appId', type=str, required=True, help="Developer app ID")
    parser.add_argument('-publicAccessKey', '--publicAccessKey', type=str, required=True, help="Developer Public Access Key")
    parser.add_argument('-privateAccessKey', '--privateAccessKey', type=str, required=True, help="Developer Private Access Key")
    parser.add_argument('-o', '--output', type=str, required=True, help="Output directory")

    args = parser.parse_args()

    sugardl = SugarDL(args.user, args.password, args.appId, args.publicAccessKey, args.privateAccessKey)
    if not sugardl.download_files(args.output):
        print("Program terminated with a fatal error")
        return -1

    print("Successfully downloaded files to {}".format(args.output))

    return 0


if __name__ == '__main__':
    sys.exit(main())
