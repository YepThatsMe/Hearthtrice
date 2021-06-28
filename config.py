LIBRARY_PATH = 'default'

def set_path(path):
    global LIBRARY_PATH
    LIBRARY_PATH = path

if __name__ == '__main__':
    set_path('asdfghj')
    print(LIBRARY_PATH)