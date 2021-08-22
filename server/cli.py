import requests as r
import json

URL = 'http://localhost:5000'
APIKEY = ''
UNAME = ''

def printlen(num, word):
    word = str(word)
    if len(word) >= num - 1:
        word = word[:num-1]
    
    print(word + ' ' * (num - len(word)), end='')

def perror(resp):
        sc = resp.status_code
        if sc == 200:
            return False
        elif sc == 500:
            print('ERROR: Internal Server Error')
        elif sc == 400:
            print('ERROR: Bad Request Body')
        elif sc == 401:
            print('ERROR: Unauthorized')
        elif sc == 403:
            print('ERROR: Forbidden')
        elif sc == 404:
            if resp.text == 'Uninitialized RID':
                print('ERROR: 초기화되지 않은 냉장고')
            else:
                print('ERROR: 올바르지 않은 냉장고 또는 섹터 값')
        elif sc == 405:
            print('ERROR: Method Not Allowed')
        else:
            print('ERROR: Unknown')
        return True

class Commands():
    def __init__(self):
        self._selection = {
            "fridge": '',
            "sector": '',
        }
    
    def get_selection(self, key):
        return self._selection[key]
    
    def list(self, tokens):
        def print_help():
            print('\nHELP LIST')
            print('fridge\t - 냉장고 목록을 표시합니다. ex) list fridge')
            print('sector\t - 선택한 냉장고에 있는 섹터 목록을 표시합니다. ex) list sector')

        if len(tokens) <= 1 or tokens[1] not in self._selection:
            print_help()
            return
        
        if tokens[1] == 'fridge':
            res = r.get(URL + '/stat', headers={'x-api-key': APIKEY})
            if perror(res):
                return
            res = res.json()

            printlen(15, "RID")
            print('ALIAS')
            for rid, alias in res.items():
                printlen(15, rid)
                print(alias)
        
        elif tokens[1] == 'sector':
            if not self._selection['fridge']:
                print('선택한 냉장고가 없습니다.')
                return
            
            res = r.get(URL + '/stat/' + self._selection['fridge'],
                        headers={'x-api-key': APIKEY})
            if perror(res):
                return
            res = res.json()

            if not res['initialized']:
                print('선택한 냉장고가 초기화되지 않았습니다.')
                return
            
            printlen(10, 'SID')
            printlen(10, 'numslot')
            print('mainslot')

            for sid, obj in res['status'].items():
                printlen(10, sid)
                printlen(10, obj['numslot'])
                print(obj['mainslot'])
        else:
            print_help()
            return


    def select(self, tokens):
        def print_help():
            print('\nHELP SELECT')
            print('fridge\t - 냉장고를 선택합니다. ex) select fridge test1234')
            print('sector\t - 섹터를 선택합니다. ex) select sector 3abee3e3')

        if len(tokens) <= 2 or tokens[1] not in self._selection:
            print_help()
            return

        selection = tokens[2]
        if tokens[1] == 'fridge':
            if selection == self._selection['fridge']:
                print('이미 선택된 냉장고:', selection)
                return
            else:
                res = r.get(URL + '/stat/' + selection,
                        headers={'x-api-key': APIKEY})
                if perror(res):
                    return
                self._selection['fridge'] = selection
                self._selection['sector'] = ''
                print('선택된 냉장고:', selection)

        elif tokens[1] == 'sector':
            if selection == self._selection['sector']:
                print('이미 선택된 섹터:', selection)
                return
            else:
                res = r.get(URL + '/stat/' + self._selection['fridge'],
                        headers={'x-api-key': APIKEY})
                if perror(res):
                    return
                res = res.json()

                if not res['initialized']:
                    print('선택한 냉장고가 초기화되지 않았습니다.')
                    return
                
                if selection not in res['status']:
                    print('올바르지 않은 섹터ID')
                    return
                else:
                    self._selection['sector'] = selection
        else:
            print_help()
            return
    
    def current(self, tokens):
        print('선택된 냉장고:', self._selection['fridge'] if self._selection['fridge'] else '없음')
        print('선택된 섹터:', self._selection['sector'] if self._selection['sector'] else '없음')

    def request(self, tokens):
        def print_help():
            print('\nHELP REQUEST')
            print('섹터의 메인슬롯 변경을 요청합니다.')
            print('ex) request 3')

        if len(tokens) == 1:
            print_help()
            return
        
        try:
            selected = int(tokens[1])
        except:
            print_help()
            return
        req = json.dumps({
                            "status": {
                                self._selection['sector']: selected
                            }
                        })
        res = r.put(URL + '/stat/' + self._selection['fridge'],
                    headers={'x-api-key': APIKEY}, data=req)
        if perror(res):
            return
        print('요청 성공')

    def interpreter(self, inp):
        tokens = inp.split(' ')
        command = tokens[0]

        if command == 'list':
            self.list(tokens)
        elif command == 'select':
            self.select(tokens)
        elif command == 'current':
            self.current(tokens)
        elif command == 'request':
            self.request(tokens)
        elif command == 'exit':
            return True
        else:
            print('command available: list, current, select, request')
        
        return False
            

if __name__ == '__main__':
    with open('key.json', 'r') as f:
        keys = json.load(f)
    
    kdict = {}

    print("API Key List:")
    for k, n in keys.items():
        kdict[n] = k
        print(f"{n}: {k}")
    
    while True:
        inp = input('Select Key: ')
        if inp in kdict:
            APIKEY = kdict[inp]
            UNAME = inp
            break
    
    print('-----'*5)
    comm = Commands()

    while True:
        print('')
        inp = input(UNAME + '@' + comm.get_selection('fridge') + ':' + comm.get_selection('sector') + '$ ')
        if comm.interpreter(inp):
            break
    
    print('Goodbye')
