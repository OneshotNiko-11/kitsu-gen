# incase u get verification email but its recommende to use this generator py file instead
import requests
import random
import string
import threading
import time
import os
import re
import json
from colorama import init, Fore

init()

def load_proxies():
    try:
        with open("proxies.txt", "r") as f:
            proxies = [line.strip() for line in f if line.strip()]
            if proxies:
                print(Fore.YELLOW + f"[*] loaded {len(proxies)} proxies")
            return proxies
    except:
        return []

def get_proxy(proxies, index):
    if not proxies:
        return None
    return proxies[index % len(proxies)]

def setup_session_proxy(session, proxy_str, use_proxies):
    if use_proxies and proxy_str:
        try:
            session.proxies.update({
                'http': f'socks5://{proxy_str}',
                'https': f'socks5://{proxy_str}'
            })
        except:
            pass
    return session

def create_temp_inbox(session):
    try:
        url = 'https://api.internal.temp-mail.io/api/v3/email/new'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        payload = {"min_name_length": 10, "max_name_length": 10}
        response = session.post(url, headers=headers, json=payload, timeout=15)

        if response.status_code != 200:
            return None

        data = response.json()
        email = data.get('email')

        if not email:
            return None

        return {'address': email}
    except:
        return None

def get_temp_mail_messages(session, email):
    try:
        url = f'https://api.internal.temp-mail.io/api/v3/email/{email}/messages'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        }
        response = session.get(url, headers=headers, timeout=15)

        if response.status_code == 200:
            messages = response.json()
            return messages if isinstance(messages, list) else []
        return []
    except:
        return []

def extract_verification_link(body_text):
    pattern = r'Confirm Email \( (https://kitsu\.app/confirm-email\?token=[a-zA-Z0-9\-_]+) \)'
    match = re.search(pattern, body_text)
    if match:
        return match.group(1)

    pattern2 = r'https://kitsu\.app/confirm-email\?token=[a-zA-Z0-9\-_]+'
    match2 = re.search(pattern2, body_text)
    if match2:
        return match2.group(0)

    return None

def wait_for_verification_email(session, email, max_wait=90):
    print(Fore.YELLOW + f"[*] waiting verification for {email}")

    for _ in range(int(max_wait/3)):
        try:
            messages = get_temp_mail_messages(session, email)

            for message in messages:
                subject = message.get('subject', '').lower()
                body_text = message.get('body_text', '')

                if 'activate' in subject or 'confirm' in subject:
                    link = extract_verification_link(body_text)
                    if link:
                        print(Fore.GREEN + f"[+] got link for {email}")
                        return link

            time.sleep(3)
        except:
            time.sleep(3)

    return None

def verify_email(session, verification_link):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
        response = session.get(verification_link, headers=headers, timeout=15, allow_redirects=True)
        if response.status_code == 200:
            return True
    except:
        pass
    return False

def generate_username():
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for _ in range(10))

def generate_password():
    uppercase = ''.join(random.choice(string.ascii_uppercase) for _ in range(3))
    lowercase = ''.join(random.choice(string.ascii_lowercase) for _ in range(5))
    numbers = ''.join(random.choice(string.digits) for _ in range(3))
    symbols = '@@'

    password = uppercase + lowercase + numbers + symbols
    password_list = list(password)
    random.shuffle(password_list)
    return ''.join(password_list)

def create_account(proxies, target_accounts, accounts_created, lock, running, proxy_index_counter, use_proxies):
    while running[0]:
        with lock:
            if accounts_created[0] >= target_accounts:
                break
            proxy_index = proxy_index_counter[0]
            proxy_index_counter[0] += 1

        proxy = get_proxy(proxies, proxy_index) if use_proxies else None
        session = requests.Session()
        session = setup_session_proxy(session, proxy, use_proxies)

        try:
            temp_mail = create_temp_inbox(session)
            if not temp_mail or 'address' not in temp_mail:
                continue

            email = temp_mail['address']
            print(Fore.GREEN + f"[*] mail: " + Fore.LIGHTMAGENTA_EX + f"{email}")

            username = generate_username()
            password = generate_password()

            url = 'https://kitsu.app/api/edge/users'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Content-Type': 'application/vnd.api+json',
                'Accept': 'application/vnd.api+json',
                'Origin': 'https://kitsu.app',
                'Referer': 'https://kitsu.app/',
                'Authorization': 'Bearer undefined',
                'X-Requested-With': 'XMLHttpRequest'
            }

            payload = {
                "data": {
                    "type": "users",
                    "attributes": {
                        "email": email,
                        "name": username,
                        "password": password
                    }
                }
            }

            response = session.post(url, headers=headers, json=payload, timeout=15)

            if response.status_code == 200 or response.status_code == 201:
                print(Fore.CYAN + f"[+] created: " + Fore.LIGHTMAGENTA_EX + f"{username}")

                verification_link = wait_for_verification_email(session, email)

                if verification_link:
                    if verify_email(session, verification_link):
                        with lock:
                            if accounts_created[0] < target_accounts:
                                accounts_created[0] += 1
                                with open("kitsu_accs.txt", "a") as f:
                                    f.write(f"{email}:{password}:{username}\n")
                                print(Fore.LIGHTGREEN_EX + f"[✓] verified: {username}")
                    else:
                        print(Fore.RED + f"[-] verify failed: {username}")
                else:
                    print(Fore.RED + f"[-] no verify link: {username}")
            else:
                print(Fore.RED + f"[-] create failed: {response.status_code}")

        except Exception as e:
            print(Fore.RED + f"[!] error: {e}")
            continue

        delay = random.uniform(3, 6)
        time.sleep(delay)

def main():
    os.system('cls' if os.name == 'nt' else 'clear')

    print(Fore.LIGHTYELLOW_EX + "Kitsu Account Generator + Email Verify")
    print(Fore.YELLOW + "[*] With email verification")

    proxies = []
    use_proxies = False

    use_proxy_input = input(Fore.LIGHTCYAN_EX + "Use proxies? (y/n): " + Fore.WHITE).lower()
    if use_proxy_input == 'y':
        proxies = load_proxies()
        if not proxies:
            print(Fore.RED + "[!] no proxies")
            return
        use_proxies = True
        print(Fore.GREEN + "[+] using proxies")
    else:
        print(Fore.YELLOW + "[*] no proxies")

    try:
        target_accounts = int(input(Fore.LIGHTCYAN_EX + "Accounts to make: " + Fore.WHITE))
        threads_count = int(input(Fore.LIGHTCYAN_EX + "Threads: " + Fore.WHITE))
    except:
        return

    accounts_created = [0]
    running = [True]
    lock = threading.Lock()
    proxy_index_counter = [0]
    threads = []

    for i in range(threads_count):
        thread = threading.Thread(target=create_account, args=(proxies, target_accounts, accounts_created, lock, running, proxy_index_counter, use_proxies), daemon=True)
        threads.append(thread)
        thread.start()

    try:
        while any(t.is_alive() for t in threads):
            time.sleep(0.5)
            if accounts_created[0] >= target_accounts:
                running[0] = False
                break
    except KeyboardInterrupt:
        running[0] = False
        print(Fore.RED + "\n[!] stopping")

    print(Fore.LIGHTGREEN_EX + f"\n✓ {accounts_created[0]} accounts")
    print(Fore.LIGHTBLUE_EX + f"[*] kitsu_accs.txt")

if __name__ == "__main__":
    main()
