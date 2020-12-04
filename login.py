import pickle
import traceback
from time import sleep

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


try:
    from epic_games_settings import hide_browsers, save_cookies
except ModuleNotFoundError:
    hide_browsers = save_cookies = 1

from local_paths import local_path
from heroku_paths import heroku_path, chrome_binary_heroku_path

path = heroku_path or local_path

def users():
    users = []
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
        try:
            with open(f'{login}.pkl', 'rb') as file:
                cookies = pickle.load(file)
                root.get('https://www.epicgames.com/id/login')
                for cookie in cookies:
                    root.add_cookie(cookie)
                root.refresh()
        except FileNotFoundError:
            print(f'{login}:No cookies found')
            root.get('https://www.epicgames.com/id/login')

        # check if logged in
        sleep(3)
        if root.current_url == 'https://www.epicgames.com/id/login':
            print(f'{login}: needs to login')
            return
        else:
            print(f'{login}: already logged in')

        # save cookies
        if save_cookies:
            with open(f'{user[0]}.pkl', 'wb') as cookies:
                pickle.dump(root.get_cookies(), cookies)
                print(f'{login}: saved cookies')
    finally:
        root.close()


if __name__ == '__main__':
    try:
        for user in users():
            epic_games_login(user)
    except:
        traceback.print_exc()
        input('Press any key to continue')