def install(modules):
    for module in modules:
        try:
            __import__(module)
        except ImportError:
            print(f"Trying to install the required module: {module}\n")
            os.system(f"python -m pip install {module}")

module_list = [
    "tqdm",
    "requests",
    "pathlib",
    "urllib",
]
try:
    import os
    import re
    import requests
    import tqdm
    import urllib
    import time
    from progress.spinner import Spinner
    import glob
except ImportError:
    try:
        install(module_list)
    except Exception as e:
        print(f'Error: {e}')

#write all beatmaps id to osu.txt
def save(pathx):
    ins = pathx
    try:
        files = os.listdir(ins)
        with open(f'osu.txt', 'a') as txt:
            for file in files:
                pattern = r'\d+'
                try:
                    result = re.findall(pattern, file)[0]
                    if int(result) > 999:
                        txt.write(f'{result}\n')
                        print(f'Write {file}')
                except:
                    print('Unable to write')
                    continue
        print(f'Total: {len(files)} files, saved text file to local script file')
    except KeyboardInterrupt:
        print('Program stopped by user')

def download(path):
    fileExist, dwn = 0, 0
    ls = []
    os.system('cls')
    with open('osu.txt', 'r') as txt:
        lines = [line.rstrip('\n') for line in txt.readlines()]
    print(f'Found {len(lines)} beatmaps!')
    os.makedirs(path, exist_ok=True)
    files = os.listdir(f'{path}')
    pattern = r'\d+'

    ls = []
    os.system('cls')
    #checking all beatmaps in osu.txt to skip duplicates
    for i, item in enumerate(lines):
        print(f'Checking all beatmaps: {i}/{len(lines)}', end = '\r')
        number = int(re.findall(pattern, item)[0])
        found = False
        for file in files:
            if str(number) in file:
                found = True
                fileExist+=1
                break
        if not found:
            #all beatmap id will be in this list
            ls.append(number)

    for i, id in enumerate(ls) if ls is not None else print('No beatmaps found.'):
        os.system('cls')
        print(f'Downloading {i}/{len(ls)}')

        #request to chimu api
        r = requests.get(f'https://api.chimu.moe/v1/download/{id}', stream=True)
        
        #exist?
        if r.headers["Content-Type"] != "application/octet-stream":
            print(f"{id} failed, download manually")
            continue
        
        #get download
        d = r.headers["Content-Disposition"]
        
        #regex for .osk form (<id> <artist> - <file name>.<osz/osk>) otherwise file cannot be oppened
        filename = urllib.parse.unquote(d.split('filename=')[1].strip(),).replace('%20', ' ')
        filename = re.sub(r'[\/\\\*:\?"\<>\|]', '', filename)
        print(f'Downloading: {filename}...')
        
        #progress bar
        total_size = int(r.headers.get('Content-Length', 0))
        block_size = 1024
        progress = tqdm.tqdm(total=total_size, unit='iB', unit_scale=True)
        
        #first create .osz file, then update that file continuously until done
        with open(f"{path}\\{filename}", "wb") as f:
            for chunk in r.iter_content(block_size):
                if chunk:
                    f.write(chunk)
                    progress.update(len(chunk))
        dwn += 1
        print('\n')
        time.sleep(0.2)
    os.system('cls')
    print(f'Beatmaps existed: {fileExist} | Beatmaps downloaded: {dwn} ')
    return

def menu(input, path):
    match input:
        case 1:
            save(path)
        case 2:
            download(path)
        case _:
            print('Invalid input!')

if __name__ == '__main__':
    while True:
        os.system("cls")
        pathz = input('Paste your osu songs path here (for example: D:\osu!): ')
        exe_files = glob.glob(f"{pathz}/*osu!.exe")
        path = pathz + "\songs"
        print(f'Current dictionary: {path}')
        if not os.path.exists(path) or not exe_files:
            print("Path does not exist or not contain osu.exe")
            time.sleep(2)
            continue
        break

    while True:
        inz = input('''
1. Save all beatmaps id to osu.txt (folder that contain this script)
2. Download all beatmaps from local osu.txt (folder that contain this script)

Exit: ctr^C
Select: ''')
        menu(int(inz), path)
        input("Press any key to continue")
        os.system('cls')
