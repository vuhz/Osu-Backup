def install(modules):
    for module in modules:
        try:
            __import__(module)
        except ImportError:
            print(f"Trying to install the required module: {module}\n")
            os.system(f"python -m pip install {module}")


module_list = ["tqdm", "requests", "pathlib", "urllib", "inquirer"]

try:
    import os
    import re
    import glob
    import time
    import json
    import random
    import urllib
    import sys as sus
    import multiprocessing
    from multiprocessing import Process, Semaphore

    import tqdm
    import inquirer
    import requests
    from progress.spinner import Spinner

    from read_collection import collection_to_dict
except ImportError:
    try:
        install(module_list)
    except Exception as e:
        print(f"Error: {e}")


class Songs:
    def __init__(self, path) -> None:
        self.path = path
        self.max_worker = 0
        pass
    def init_config(self):
        with open("config.json", "r") as f:
            data = json.load(f)
            self.max_worker = int(data["max_worker"])
    # write all beatmaps id to osu.txt
    def save(self):
        try:
            files = os.listdir(self.path)
            with open(f"osu.txt", "w") as txt:
                for file in sorted(files):
                    pattern = r"\d+"
                    try:
                        result = re.findall(pattern, file)[0]
                        if int(result) > 0:
                            txt.write(f"{result}\n")
                            print(f"Write {file}")
                    except:
                        print("Unable to write")
                        continue
            print(f"Total: {len(files)} files, saved text file to local script file")
        except KeyboardInterrupt:
            print("Program stopped by user")

    def get_from_id(self, path, id, i, limit):
        r = requests.get(f"https://api.chimu.moe/v1/download/{id}", stream=True)
        if r.headers["Content-Type"] != "application/octet-stream":
            print(f"{id} failed, download manually")
            return
        d = r.headers["Content-Disposition"]
        filename = urllib.parse.unquote(d.split("filename=")[1].strip()).replace("%20", " ")
        filename = re.sub(r'[\/\\\*:\?"\<>\|]', "", filename)
        print(f"[{i+1}/{limit}] - Downloading: {filename}...")
        with open(f"{path}\\{filename}", "wb") as f:
            for chunk in r.iter_content(1024):
                if chunk:
                    f.write(chunk)
        return id
    
    def download(self):
        fileExist, dwn = 0, 0
        ls = []
        os.system("cls")
        try:
            with open("osu.txt", "r") as txt:
                lines = [line.rstrip("\n") for line in txt.readlines()]
        except FileNotFoundError:
            print('osu.txt not found!')
            return
        print(f"Found {len(lines)} beatmaps!")
        os.makedirs(self.path, exist_ok=True)
        files = os.listdir(f"{self.path}")
        pattern = r"\d+"

        ls = []
        os.system("cls")
        for i, item in enumerate(lines):
            print(f"Checking all beatmaps: {i}/{len(lines)}", end="\r")
            number = int(re.findall(pattern, item)[0])
            found = False
            for file in files:
                if str(number) in file:
                    found = True
                    fileExist += 1
                    break
            if not found:
                ls.append(number)
        random.shuffle(ls)

        currnt_worker = 0
        for i, id in enumerate(ls) if ls is not None else print("No beatmaps found."):
            if currnt_worker == self.max_worker:
                p.join()
                currnt_worker = 0
            p = Process(target=self.get_from_id, args=(self.path, id, i, len(ls),))
            p.start()
            currnt_worker += 1
            dwn += 1
        try:
            p.join()
        except UnboundLocalError:
            pass
        print(f"Beatmaps existed: {fileExist} | Beatmaps downloaded: {dwn} ")
        return


class Collection:
    def __init__(self, path) -> None:
        self.secret = "xxx"
        self.oid = 22188
        self.max_worker = 0
        self.path: str = path
        self.token = ""
        self.collections = {}
        self.pool = multiprocessing.Pool(3)
        self.init_config()
        pass

    def init_config(self):
        with open("config.json", "r") as f:
            data = json.load(f)
            self.secret = data["osu_secret"]
            self.oid = data["osu_app_id"]
            self.max_worker = int(data["max_worker"])

    def get_map_collection(self) -> dict:
        self.collections = collection_to_dict(
            f"{self.path.strip('/songs')}\\collection.db"
        )
        return self.collections

    def token_request(self) -> str:
        token_auth = "https://osu.ppy.sh/oauth/token"
        params = {
            "client_id": self.oid,
            "client_secret": self.secret,
            "grant_type": "client_credentials",
            "scope": "public",
        }
        token = requests.post(token_auth, params)
        self.token = token.json()["access_token"]
        return token.json()["access_token"]

    def get_name(self, checksum) -> str:
        beatmaps_url = "https://osu.ppy.sh/api/v2/beatmaps/lookup"
        headers = {"Authorization": f"Bearer {self.token}"}
        params = {
            "checksum": checksum,
        }
        beatmap = requests.get(beatmaps_url, params, headers=headers)
        return beatmap.json()["beatmapset"]

    def save_collection(self) -> None:
        self.get_map_collection()
        with open("hash.txt", "wb") as f:
            for collection in self.collections["collections"]:
                for hash in collection["hashes"]:
                    f.write(hash.encode("utf-8") + b"\n")
                    print(f"Wrote {hash} from {collection['name']}")

    def get_from_id(self, path, id, i, limit):
        r = requests.get(f"https://api.chimu.moe/v1/download/{id}", stream=True)
        if r.headers["Content-Type"] != "application/octet-stream":
            print(f"{id} failed, download manually")
            return
        d = r.headers["Content-Disposition"]
        filename = urllib.parse.unquote(d.split("filename=")[1].strip()).replace("%20", " ")
        filename = re.sub(r'[\/\\\*:\?"\<>\|]', "", filename)
        print(f"[{i+1}/{limit}] - Downloading: {filename}...")
        with open(f"{path}\\{filename}", "wb") as f:
            for chunk in r.iter_content(1024):
                if chunk:
                    f.write(chunk)
        return id

    def download(self):
        prev = ""
        id = ""
        currnt_worker = 0
        manager = multiprocessing.Manager()
        prev = manager.dict()
        self.token_request()

        os.system("cls")
        try:
            with open("hash.txt", "r") as txt:
                lines = [line.rstrip("\n") for line in txt.readlines()]
        except UnboundLocalError:
            print("hash.txt not found!")
            return
        print(f"Found {len(lines)} beatmaps!")
        os.makedirs(self.path, exist_ok=True)
        random.shuffle(lines)
        limit = input("Check how much beatmaps to download? (Blank to check all) : ")
        if limit == "" or limit == " ":
            limit = len(lines)
        for i, hash in (enumerate(lines[: int(limit)]) if lines is not None else print("No beatmaps found.")):
            try:
                if currnt_worker == self.max_worker:
                    p.join()
                    currnt_worker = 0
                try:
                    id = self.get_name(hash)["id"]
                    if prev == id:
                        continue
                except:
                    prev = id
                    continue
                p = Process(target=self.get_from_id, args=(self.path, id, i, limit,))
                p.start()
                prev = id
                currnt_worker += 1
            except Exception as e:
                print(f"{e} - Terminate")
                return
        p.join()
        print("Done!")

    # https://stackoverflow.com/questions/59232822/python-multiprocessing-pool-raise-valueerrorpool-not-running-valueerror-po
    def __getstate__(self):
        self_dict = self.__dict__.copy()
        del self_dict['pool']
        return self_dict

    def __setstate__(self, state):
        self.__dict__.update(state)


class Menu:
    def __init__(self) -> None:
        pass

    def menu(self):
        while True:
            os.system("cls")
            pathz = input("Paste your osu songs path here (for example: D:\osu!): ")
            exe_files = glob.glob(f"{pathz}/*osu!.exe")
            path = os.path.join(pathz, "songs")
            print(f"Current dictionary: {path}")
            if not os.path.exists(path) or not exe_files:
                print("Path does not exist or does not contain osu.exe")
                time.sleep(2)
                continue
            break

        while True:
            questions = [
                inquirer.List(
                    "choice",
                    message="Select an option",
                    choices=[
                        ("Save all beatmap from songs id to osu.txt", 1),
                        ("Download all beatmap from local osu.txt", 2),
                        ("Save all beatmaps from collections.db to hash.txt", 3),
                        ("Download all breatmap from local hash.txt", 4),
                        ("Exit", 5),
                    ],
                ),
            ]

            answers = inquirer.prompt(questions)
            choice = answers["choice"]

            self.choice(choice, path)

            input("Press any key to continue")
            os.system("cls")

    def choice(self, input, path):
        song = Songs(path)
        collection = Collection(path)

        match input:
            case 1:
                song.save()
            case 2:
                song.download()
            case 3:
                collection.save_collection()
            case 4:
                collection.download()
            case 5:
                sus.exit()
            case _:
                print("Invalid input!")

if __name__ == '__main__': 
    # https://stackoverflow.com/questions/7067787/python-multiprocessing-processes-become-copies-of-the-main-process-when-run-fr
    multiprocessing.freeze_support()
    menu = Menu()
    menu.menu()