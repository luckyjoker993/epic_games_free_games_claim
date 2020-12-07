import json
import traceback
from time import sleep

from dropbox.exceptions import ApiError
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


try:
    from epic_games_settings import hide_browsers, save_cookies
except ModuleNotFoundError:
    hide_browsers = save_cookies = 1

from download_upload import download, upload

from local_paths import local_path
from heroku_paths import heroku_path, chrome_binary_heroku_path, drop_box_token

path = heroku_path or local_path


def users():
    users = []
    if drop_box_token:
        print('Downloading login.txt from Dropbox')
        file_bytes = download(drop_box_token, 'login.txt')
        login_password_list = file_bytes.decode().split()
        if len(login_password_list) % 2 != 0:
            print('There should be same number of logins and password')
            raise IndexError
        while len(login_password_list):
            password = login_password_list.pop()
            login = login_password_list.pop()
            users.append((login, password))
        return users
    else:
        print('Reading local login.txt file')
        try:
            with open('login.txt', 'r') as file:
                while True:
                    login = file.readline().strip()
                    if not login:
                        break
                    password = file.readline().strip()
                    users.append((login, password))
            return users
        except FileNotFoundError:
            print('login.txt file should be in same directory')
            raise


def epic_games_login(user):
    try:
        login, password = user
        options = Options()
        if chrome_binary_heroku_path:
            options.binary_location = chrome_binary_heroku_path
        if hide_browsers:
            options.add_argument('--headless')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-position=-2000,0')

        root = webdriver.Chrome(executable_path=path, options=options)

        # Load cookies
        if drop_box_token:
            # load dropbox cookies
            try:
                root.get('https://www.epicgames.com/id/login')
                print(f'{login}: Getting cookies from dropbox')
                cookies_bytes = download(drop_box_token, f'{login}.json')
                cookies = json.loads(cookies_bytes)
                for cookie in cookies:
                    try:
                        cookie['expiry'] += 600  # extend cookie
                    except KeyError:
                        pass
                    root.add_cookie(cookie)
                print(f'{login}: Cookies loaded from dropbox')
                root.refresh()
            except ApiError as e:
                print(f'{login}: {e}')
        else:
            # Load local cookies
            try:
                root.get('https://www.epicgames.com/id/login')
                print(f'{login}: Getting cookies from local')
                with open(f'{login}.json', 'r') as file:
                    cookies = json.load(file)
                    for cookie in cookies:
                        try:
                            cookie['expiry'] += 600  # extend cookie
                        except KeyError:
                            pass
                        root.add_cookie(cookie)
                    print(f'{login}: Cookies loaded')
                    root.refresh()
            except FileNotFoundError:
                print(f'{login}: No cookies found')

        # check if logged in
        sleep(3)
        if root.current_url == 'https://www.epicgames.com/id/login':
            print(f'{login}: needs to login')
            return
        else:
            print(f'{login}: already logged in')

        # save cookies
        if save_cookies:
            if drop_box_token:
                # upload cookies to dropbox
                cookies = json.dumps(root.get_cookies())
                upload(drop_box_token, f'{login}.json', bytes(cookies, encoding='utf-8'))
                print(f'{login}: Cookies uploaded to dropbox')
            else:
                # Save cookies localy
                with open(f'{user[0]}.json', 'w') as cookies:
                    json.dump(root.get_cookies(), cookies)
                    print(f'{login}: Cookies saved')
    finally:
        root.close()


if __name__ == '__main__':
    try:
        for user in users():
            epic_games_login(user)
    except:
        traceback.print_exc()
        # input('Press any key to continue')
