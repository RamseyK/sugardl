import os
import requests
import urllib3
import datetime
import time
import sys
import argparse
import traceback
from dateutil import parser as dateutil_parser
from collections import defaultdict
from xml.etree import cElementTree as ET
from xml.dom import minidom
from urllib3.exceptions import InsecureRequestWarning


BASE_URL = 'https://api.sugarsync.com/'


# From: https://stackoverflow.com/questions/2148119
def etree_to_dict(t):
    d = {t.tag: {} if t.attrib else None}
    children = list(t)
    if children:
        dd = defaultdict(list)
        for dc in map(etree_to_dict, children):
            for k, v in dc.items():
                dd[k].append(v)
        d = {t.tag: {k:v[0] if len(v) == 1 else v for k, v in dd.items()}}
    if t.attrib:
        d[t.tag].update(('@' + k, v) for k, v in t.attrib.items())
    if t.text:
        text = t.text.strip()
        if children or t.attrib:
            if text:
              d[t.tag]['#text'] = text
        else:
            d[t.tag] = text
    return d


class SugarDL(object):

    def __init__(self, username, password, appId, publicAccessKey, privateAccessKey):

        self.username = username
        self.password = password
        self.appId = appId
        self.publicAccessKey = publicAccessKey
        self.privateAccessKey = privateAccessKey

        self._default_headers = {
            'User-Agent': 'SugarDL',
            'Host': 'api.sugarsync.com',
            'Content-Type': 'application/xml'
        }
        urllib3.disable_warnings(InsecureRequestWarning)

        self._output_path = None

        # Access Vars
        self._refresh_token = None
        self._access_token = None
        self._access_token_expiry = None

        # User Information
        self._user_id = None
        self._user_sync_folders_url = None

        # Folder information
        self._folder_metadata = []

    def download_files(self, output, replace=False):
        """
        Downloads all files from the SugarSync account to the provided output folder

        :param output: Destination top level output folder
        :param replace: If True, replace contents in the output folder even if it exists. Default, skip any existing files
        :return: True if successful, False otherwise
        """

        try:

            # Create output directory
            # self._output_path = os.path.join(output,
            #                                  "sugardl_{}".format(datetime.datetime.now().strftime("%Y%m%d_%H%M%S")))
            # os.makedirs(self._output_path)
            # Just write to the provided output directory
            self._output_path = output

            #####
            # Authenticate: getting a refresh token, then an access token
            #####
            print("Authenticating..")
            self._get_refresh_token()
            self._get_access_token()

            #####
            # User Info
            #####
            self._get_user_info()

            #####
            # Get all folder metadata prior to download
            #####
            self._get_sync_folders()

            #####
            # Download: Recursively download all syncfolder contents
            #####
            for folder in self._folder_metadata:
                print("== SYNC FOLDER DOWNLOAD: {} ==".format(folder['displayName']))
                self._download_folder_contents(folder['contents'], "{}/{}".format(self._output_path, folder['displayName']), start_idx=0, replace=replace)
                print("")

        except Exception as e:
            print("Error in download_files: {}".format(traceback.print_exc()))
            return False

        return True

    def _get_refresh_token(self):
        """
        Retrieves Refresh Token, a prerequisite for the Access Token. Useful so we dont need the user/pass after this
        https://www.sugarsync.com/dev/api/method/create-refresh-token.html

        :return:
        """

        doc = minidom.Document()
        root = doc.createElement('appAuthorization')
        doc.appendChild(root)
        user = doc.createElement('username')
        user.appendChild(doc.createTextNode(self.username))
        root.appendChild(user)
        pw = doc.createElement('password')
        pw.appendChild(doc.createTextNode(self.password))
        root.appendChild(pw)
        application = doc.createElement('application')
        application.appendChild(doc.createTextNode(self.appId))
        root.appendChild(application)
        aki = doc.createElement('accessKeyId')
        aki.appendChild(doc.createTextNode(self.publicAccessKey))
        root.appendChild(aki)
        pak = doc.createElement('privateAccessKey')
        pak.appendChild(doc.createTextNode(self.privateAccessKey))
        root.appendChild(pak)
        data = doc.toprettyxml()

        resp = requests.post(BASE_URL + "app-authorization", data=data, headers=self._default_headers, verify=False)
        if resp.status_code >= 300:
            raise Exception("Failed to authorize app: {}".format(resp))

        # Save off the refresh token
        self._refresh_token = resp.headers.get('Location', None)

    def _get_access_token(self):
        """
        Requests Access Token using the Refresh Token. Access Token is required for all future requests
        https://www.sugarsync.com/dev/api/method/create-auth-token.html

        :return:
        """

        self._access_token = None
        if not self._refresh_token:
            raise ValueError("Refresh Token not set")

        doc = minidom.Document()
        root = doc.createElement('tokenAuthRequest')
        doc.appendChild(root)
        aki = doc.createElement('accessKeyId')
        aki.appendChild(doc.createTextNode(self.publicAccessKey))
        root.appendChild(aki)
        pak = doc.createElement('privateAccessKey')
        pak.appendChild(doc.createTextNode(self.privateAccessKey))
        root.appendChild(pak)
        rt = doc.createElement('refreshToken')
        rt.appendChild(doc.createTextNode(self._refresh_token))
        root.appendChild(rt)
        data = doc.toprettyxml()

        resp = requests.post(BASE_URL + "authorization", data=data, headers=self._default_headers, verify=False)
        if resp.status_code >= 300:
            raise Exception("Failed to claim access token: {}".format(resp))

        vals = etree_to_dict(ET.XML(resp.content.decode('utf-8')))

        self._access_token = resp.headers.get('Location', None)
        if not self._access_token:
            raise ValueError("Unable to get access token")

        self._user_id = os.path.basename(vals.get('authorization').get('user'))

        # Always set the expiry 30 minutes from now so we dont have to deal with parsing timezones
        # self._access_token_expiry = dateutil_parser.parse(vals.get('authorization').get('expiration'))
        self._access_token_expiry = datetime.datetime.utcnow() + datetime.timedelta(minutes=30)

    def _get_user_info(self):
        """
        Retrieves user information to include sync folders
        https://www.sugarsync.com/dev/api/method/get-user-info.html

        :return:
        """

        if not self._refresh_token:
            raise ValueError("Refresh Token not set")

        # Add access token to the headers
        add_headers = dict(self._default_headers)
        add_headers['Authorization'] = self._access_token

        resp = requests.get(BASE_URL + "user/{}".format(self._user_id), headers=add_headers, verify=False)
        if resp.status_code >= 300:
            raise Exception("Failed to claim access token: {}".format(resp))

        vals = etree_to_dict(ET.XML(resp.content.decode('utf-8')))

        # Print generic user info
        print("")
        print("== USER INFO ==")
        print("Username: {}".format(vals.get('user').get('username')))
        print("Nickname: {}".format(vals.get('user').get('nickname')))
        print("Usage: {} MB / {} MB".format(int(int(vals.get('user').get('quota').get('usage')) / (1024*1024)),
                                            int(int(vals.get('user').get('quota').get('limit')) / (1024*1024))))
        print("")

        # Grab folder ids we care about
        self._user_sync_folders_url = vals.get('user').get('syncfolders')

    def _get_sync_folders(self):
        """
        Retrieves metadata on all sync folders
        https://www.sugarsync.com/dev/api/method/get-syncfolders.html

        :return:
        """

        if not self._user_sync_folders_url:
            raise ValueError("User sync folders URL not retrieved")

        if not self._refresh_token:
            raise ValueError("Refresh Token not set")

        # Add access token to the headers
        add_headers = dict(self._default_headers)
        add_headers['Authorization'] = self._access_token

        resp = requests.get(self._user_sync_folders_url, headers=add_headers, verify=False)
        if resp.status_code >= 300:
            raise Exception("Failed to claim access token: {}".format(resp))

        vals = etree_to_dict(ET.XML(resp.content.decode('utf-8')))

        # Print and store relevant sync folder information
        print("== SYNC FOLDERS ==")
        for folder in vals.get('collectionContents').get('collection'):
            print("Folder: {}".format(folder.get('displayName')))
            self._folder_metadata.append(folder)

        print("")

    def _download_folder_contents(self, folder_uri, relpath, start_idx=0, replace=False):
        """
        Recursively downloads all file content within a folder
        https://www.sugarsync.com/dev/api/method/get-folder-info.html

        :param folder_uri: URI of the target folder
        :param relpath: Relative path to the folder from the root the users SugarSync profile
        :param start_idx: Item index to start downloading at
        :param replace: If True, replace file contents if the file already exists. Otherwise, leave alone
        :return:
        """

        if not self._access_token:
            raise ValueError("Access Token not set")

        # Create the folder in the output dir if it doesnt exist
        if not os.path.exists(relpath):
            print("Creating folder: {}".format(relpath))
            os.makedirs(relpath)

        # Add access token to the headers
        add_headers = dict(self._default_headers)
        add_headers['Authorization'] = self._access_token

        resp = requests.get(folder_uri, headers=add_headers, params={'start': start_idx}, verify=False)
        if resp.status_code >= 300:
            raise Exception("Failed to claim access token: {}".format(resp))

        vals = etree_to_dict(ET.XML(resp.content.decode('utf-8')))

        # Download all top level files
        ret_files = vals.get('collectionContents', {}).get('file', list())
        if isinstance(ret_files, dict):
            # Case when there is only a single file
            files = []
            files.append(ret_files)
        else:
            files = ret_files

        for f in files:

            try:
                filepath = "{}/{}".format(relpath, f['displayName'])

                if not replace and os.path.exists(filepath):
                    print("File already exists, skipping {}".format(filepath))
                    continue

                print("Downloading: {}".format(filepath))

                self._download_file_contents(f, filepath)
            except:
                print("Error downloading {}: {}".format(f, traceback.print_exc()))

        # If there are more than 500 items, recursively call on this same folder but start at start_idx+500
        item_count = len(vals.get('collectionContents', {}).get('collection', list())) + len(
            vals.get('collectionContents', {}).get('file', list()))
        if item_count >= 500:
            self._download_folder_contents(folder_uri, relpath, start_idx=start_idx+500, replace=replace)

        # Download all folders
        subfolders_ret = vals.get('collectionContents', {}).get('collection', list())
        if isinstance(subfolders_ret, dict):
            # Case when there is only one subfolder
            subfolders = []
            subfolders.append(subfolders_ret)
        else:
            subfolders = subfolders_ret

        for subfolder in subfolders:
            try:
                self._download_folder_contents(subfolder['contents'], relpath + "/" + subfolder['displayName'], replace=replace)
            except:
                print("Error downloading subfolder: {}".format(traceback.print_exc()))

    def _download_file_contents(self, file_metadata, local_filepath):
        """
        Downloads file contents
        https://www.sugarsync.com/dev/api/method/get-file-data.html

        :param file_metadata:
        :param local_filepath: Full path to write file data to
        :return:
        """

        # For every file download request, lets make sure the access token expiration hasnt passed
        # If so, refresh the access token
        if datetime.datetime.utcnow() > self._access_token_expiry:
            print("Refreshing access token..")
            self._get_access_token()

        if not self._access_token:
            raise ValueError("Access Token not set")

        # Dont bother trying to get file data if its not on the server
        if file_metadata['presentOnServer'] != 'true':
            print("Skipping file that isn't present on the server: ")
            return

        # Add access token to the headers
        add_headers = dict(self._default_headers)
        add_headers['Authorization'] = self._access_token

        resp = requests.get(file_metadata['fileData'], headers=add_headers, verify=False)
        if resp.status_code >= 300:
            raise Exception("Failed to claim access token: {}".format(resp))

        # Write file contents out
        with open(local_filepath, "wb") as fh:
            fh.write(resp.content)

        # Set modified date
        date_modified = time.mktime(dateutil_parser.parse(file_metadata['lastModified']).timetuple())
        os.utime(local_filepath, (date_modified, date_modified))


def main():
    parser = argparse.ArgumentParser(description="A tool to automate downloading all files from your SugarSync account")
    parser.add_argument('-u', '--user', type=str, required=True, help="SugarSync Username/Email")
    parser.add_argument('-p', '--password', type=str, required=True, help="Password")
    parser.add_argument('-a', '--appId', type=str, required=True, help="Developer app ID")
    parser.add_argument('-publicAccessKey', '--publicAccessKey', type=str, required=True, help="Developer Public Access Key")
    parser.add_argument('-privateAccessKey', '--privateAccessKey', type=str, required=True, help="Developer Private Access Key")
    parser.add_argument('-o', '--output', type=str, required=True, help="Output directory where files will be written to")
    parser.add_argument('-r', '--replace', type=bool, required=False, default=False, help="Replace contents in target directory if they already exist, otherwise leave alone")

    args = parser.parse_args()

    sugardl = SugarDL(args.user, args.password, args.appId, args.publicAccessKey, args.privateAccessKey)
    if not sugardl.download_files(args.output, replace=args.replace):
        print("Program terminated with a fatal error")
        return -1

    print("Successfully downloaded files to {}".format(args.output))

    return 0


if __name__ == '__main__':
    sys.exit(main())
