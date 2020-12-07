from dropbox import Dropbox
from dropbox.files import WriteMode

def download(token, file_name, path='/'):
    dbx = Dropbox(token)
    meta, data = dbx.files_download(path+file_name)
    return data.content


def upload(token, file_name, file_data, path='/'):
    dbx = Dropbox(token)
    dbx.files_upload(file_data, path+file_name, mode=WriteMode.overwrite)
