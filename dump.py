import json
import argparse
import pathlib
import sys
import re
import sqlite3
import collections.abc
import typing as ty
import datetime

import mozidb

class IDBObjectWrapper(collections.abc.Mapping):
	def __init__(self, conn: mozidb.IndexedDB):
		self._conn = conn
	
	def __getitem__(self, name: str) -> object:
		return self._conn.read_object(name)
	
	def __iter__(self) -> ty.Iterator[object]:
		yield from self._conn.list_objects()
	
	def __len__(self) -> int:
		return self._conn.count_objects()
	
	def __repr__(self) -> str:
		inner_repr = ", ".join(repr(k) + ": " + repr(v) for k, v in self.items())
		return f"{{{inner_repr}}}"
	
	def keys(self) -> ty.List[object]:
		return self._conn.list_objects()
	
	def items(self) -> ty.Iterable[ty.Tuple[object, object]]:
		return self._conn.read_objects().items()
	
	def values(self) -> ty.Iterable[object]:
		return self._conn.read_objects().values()

	def read_object(self, key_name: object) -> ty.Iterable[object]:
		return self._conn.read_object(key_name)

def main():
    arg_parser = argparse.ArgumentParser(
        description=""
        "Extracts URL history timeline of browser VPN extensions from browser artifacts.\n\n"
        "This Python code made for Linux.\n"
        "Copy your DB path & history file from Host Window to Linux.\n\n"

        "[*] Examples of DB path\n"
        "- Chrome\nC:\\Users\\TEMP\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\Local Extension Settings\\bihmplhobchoageeokmgbdihknkjbknd\\\n"
        "- Edge\nC:\\Users\TEMP\\AppData\Local\\Microsoft\\Edge\\User Data\\Default\\Local Extension Settings\\ighhnpmaabelnfcbbkijikgghajbiaml\\\n"
        "- Firefox\nC:\\Users\\TEMP\\AppData\\Roaming\\Mozilla\\Firefox\\Profiles\\nf7bnva7.default-release\\storage\\default\\moz-extension+++414217d9-0ac3-4855-a542-18a759eddbe5^userContextId=4294967295\idb\\\n"

        "\n[*] Examples of history file\n"
        "- Chrome\nC:\\Users\\TEMP\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\History\n"
        "- Edge\nC:\\Users\TEMP\\AppData\Local\\Microsoft\\Edge\\User Data\\Default\\History\n"
        "- Firefox\nC:\\Users\\TEMP\\AppData\\Roaming\\Mozilla\\Firefox\\Profiles\\nf7bnva7.default-release\\places.sqlite",
        formatter_class=argparse.RawTextHelpFormatter
    )
    arg_parser.add_argument(
        "--browser", 
        help="Type of Browser - one of (Chrome, Edge, Firefox)"
    )
    arg_parser.add_argument(
        "--extension",
        help="Type of extension - one of (TouchVPN, ZenMate, Browsec)"
    )
    arg_parser.add_argument(
        "--dbpath",
        help="Path of DB in your Linux"
    )
    arg_parser.add_argument(
        "--history",
        help="Path of history file in your Linux"
    )
    args = arg_parser.parse_args()

    if(int(bool(args.browser)) + int(bool(args.extension)) + int(bool(args.dbpath)) + int(bool(args.history))) != 4:
        arg_parser.error("Exactly --browser, --extension, --dbpath, --history must be used")
        return 1

    if(args.browser.lower() not in ('chrome','edge','firefox') or
       args.extension.lower() not in ('touchvpn', 'zenmate', 'browsec')):
        arg_parser.error("Exactly\t--browser must be one of (chrome, edge, firefox)\n"
                 "\t\t\t--extension must be one of (TouchVPN, ZenMate, Browsec)")
        return 1

    if(args.extension.lower() == 'touchvpn'):
        if(args.browser.lower() in ('chrome', 'edge')):
            con = connection(args)
            chrome_create_table(con, args.history)
            chrome_touchVPN(args,con)
            create_result(con)
        elif(args.browser.lower() == 'firefox'):
            con = connection(args)
            firefox_create_table(con, args.history)
            firefox_touchVPN(args, con)
            create_result(con)
        else:
            print("[!] arguments error. please check your browser arg")
    elif(args.extension.lower() == 'zenmate'):
        if(args.browser.lower() in ('chrome', 'edge')):
            con = connection(args)
            chrome_create_table(con, args.history)
            chrome_zenmate(args,con)
            create_result(con)
        elif(args.browser.lower() == 'firefox'):
            con = connection(args)
            firefox_create_table(con, args.history)
            if(firefox_zenmate(args, con)):
                create_result(con)
        else:
            print("[!] arguments error. please check your browser arg")
    elif(args.extension.lower() == 'browsec'):
        if(args.browser.lower() in ('chrome', 'edge')):
            con = connection(args)
            chrome_create_table(con, args.history)
            chrome_browsec(args,con)
            create_result(con)
        elif(args.browser.lower() == 'firefox'):
            con = connection(args)
            firefox_create_table(con, args.history)
            firefox_browsec(args, con)
            create_result(con)
        else:
            print("[!] arguments error. please check your browser arg")
    else:
        print("[!] arguments error. please check your extension arg")
        
def connection(args):
    try:
        con = sqlite3.connect('%s_%s_%s.sqlite'%(args.browser, args.extension, datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S')))
        return con
    except sqlite3.Error:
        print(sqlite3.Error)

def chrome_create_table(con, history):
    cursor_db = con.cursor()

    cursor_db.execute('ATTACH DATABASE "%s" AS history'%history)

    sql = '''CREATE TABLE history AS SELECT
        history.visits.id, visit_time / 1000000 -11644473600 as `visit_time`, history.urls.url, 
        history.urls.title FROM history.visits left join urls
        on history.visits.url = history.urls.id ORDER BY visit_time ASC'''
    cursor_db.execute(sql)

    cursor_db.execute("CREATE TABLE vpn(id integer, startTS INTEGER, stopTS, Proxy LONGVARCHAR)")

    con.commit()

def firefox_create_table(con, history):
    cursor_db = con.cursor()

    cursor_db.execute('ATTACH DATABASE "%s" AS history'%history)

    sql = '''CREATE TABLE history AS SELECT
        history.moz_historyvisits.id, history.moz_historyvisits.visit_date / 1000000 as `visit_time`, history.moz_places.url, 
        history.moz_places.title FROM history.moz_historyvisits left join moz_places
        on history.moz_historyvisits.place_id = history.moz_places.id ORDER BY visit_time ASC'''
    cursor_db.execute(sql)

    cursor_db.execute("CREATE TABLE vpn(id integer, startTS INTEGER, stopTS, Proxy LONGVARCHAR)")

    con.commit()

def insert_one(con, one_data):
    cursor_db = con.cursor()
    cursor_db.execute("INSERT INTO VPN(id, startTS, stopTS, Proxy) VALUES(?, ?, ?, ?)", one_data)
    con.commit()

def create_result(con):
    cursor_db = con.cursor()
    sql = '''
    CREATE TABLE VPN_HISTORY AS SELECT
    datetime(history.visit_time, 'unixepoch', 'localtime') as visit_time, 
    history.url, history.title, vpn.Proxy
    FROM history left join vpn
    WHERE history.visit_time between vpn.startTS and vpn.stopTS
    '''
    cursor_db.execute(sql)
    con.commit()

def create_zenmate_proxy_list(con):   
    cursor_db = con.cursor()
    cursor_db.execute("CREATE TABLE proxy_list(id integer, country_code LONGVARCHAR, URLs LONGVARCHAR, IPs LONGVARCHAR)")

    json_object = None
    with open('zenmate_proxy_list.json') as f:
        json_object = json.load(f)
    
    idx=1
    for obj in json_object:
        for node in obj['nodes']:
            data = [idx, node['countrycode'], node['dnsname'], node['serverLookup']]
            cursor_db.execute("INSERT INTO proxy_list(id, country_code, URLs, IPs) VALUES(?, ?, ?, ?)", data)
            idx=idx+1
    con.commit()

def chrome_touchVPN(args, con):
    print("[*] args \t\t: " + str(args))
    
    log_file_name = [x for x in pathlib.Path(args.dbpath).glob("*.log")][0]
    print("[*] log_file_name\t: " + str(log_file_name))
    with open(log_file_name, encoding='utf-8', errors='ignore') as f:
        logs = f.read()
        idx=logs.find('Proxy.Status.status')
        id_num = 1
        is_start=True
        one_data = [1, 0, 1999999999, 'null']
        while(1):
            ts_idx = logs[:idx].rfind('\"ts\"')
            ts = logs[ts_idx+5:ts_idx+16]
            ts = ts[0]+ts[2:]    
            st_idx = logs[idx:].find('\"status\"')
            status = logs[idx+st_idx+10:idx+st_idx+13]
            if status == 'con':
                is_start=True
            else :
                is_start=False

            p = re.compile('[^ \\t\\r\\n\\v\\f\"]+.com')
            res = p.findall(logs[idx:idx+800])
            
            res_str = ', '.join(s for s in res)

            if(is_start):
                one_data = [id_num, int(ts), 1999999999, res_str]
            else:
                one_data[2] = int(ts)
                insert_one(con, tuple(one_data))
                id_num = id_num+1
                
            logs = logs[idx+1:]
            idx=logs.find('Proxy.Status.status')
            if(idx==-1):
                break

    print("[*] result DB dumped")

def firefox_touchVPN(args, con):
    print("[*] args \t\t: " + str(args))
    sqlite_file_name = [x for x in pathlib.Path(args.dbpath).glob("*.sqlite")][-1]
    print("[*] sqlite_file_name\t: " + str(sqlite_file_name))

    with mozidb.IndexedDB(sqlite_file_name) as conn:
        print("[*] Proxy Status\t: " + IDBObjectWrapper(conn).read_object('Proxy.Status.status').get('status'))

        if(IDBObjectWrapper(conn).read_object('Reporting.Internal.queue')!=[]):
            ts = IDBObjectWrapper(conn).read_object('Reporting.Internal.queue')[-1].get('payload').get('ts')
            
            if(IDBObjectWrapper(conn).read_object('Proxy.Status.status').get('status') == 'connected'):
                print('[!] caution -> There is no timestamp for VPN-stop, so the VPN_HISTORY includes all of the history after VPN-start')
                res_str = ', '.join(s.get('address') for s in IDBObjectWrapper(conn).read_object('Proxy.Servers.active'))
                one_data = [1, int(ts/1000), 1999999999, res_str]
                insert_one(con, tuple(one_data))
            else:
                print('[!] caution -> There is no timestamp for VPN-start, so the VPN_HISTORY includes all of the history until VPN-stop')
                res_str = ', '.join(s.get('address') for s in IDBObjectWrapper(conn).read_object('Proxy.Config.config').get('free'))
                one_data = [1, 0, int(ts/1000), res_str]
                insert_one(con, tuple(one_data))
        else:
            print("[!] error - There is no timestamp")
        
        print("[*] result DB dumped")

def chrome_zenmate(args,con):
    create_zenmate_proxy_list(con)

    print("[*] args \t\t: " + str(args))
    log_file_name = [x for x in pathlib.Path(args.dbpath).glob("*.log")][0]
    print("[*] log_file_name\t: " + str(log_file_name))

    with open(log_file_name, encoding='utf-8', errors='ignore') as f:
        logs = f.read()
        idx=logs.find('proxyCountry')
        res = []
        one_data = [1, 0, 1999999999, 'null']
        id_num = 1

        while(1):   
            c_code = logs[idx+14:idx+16]
            ts_idx = idx + logs[idx:].find('dateConnected')
            ts = logs[ts_idx+15:ts_idx+38]
            ts = int(datetime.datetime.fromisoformat(ts).timestamp()+32400)     # utc+9
            res.append([id_num, ts, 1999999999, c_code])

            if(id_num != 1):
                res[-2][2] = ts
                one_data = res[-2]
                insert_one(con, tuple(one_data))

            logs = logs[idx+1:]
            idx=logs.find('proxyCountry')
            if(idx==-1):
                insert_one(con, tuple(res[-1]))
                break
            id_num = id_num+1

    print('[!] caution -> There is no timestamp for VPN-stop, so the VPN_HISTORY includes all of the history between timestamps for VPN-start')
    print("[*] result DB dumped")

def firefox_zenmate(args, con):
    create_zenmate_proxy_list(con)

    print("[*] args \t\t: " + str(args))
    sqlite_file_name = [x for x in pathlib.Path(args.dbpath).glob("*.sqlite")][-1]
    print("[*] sqlite_file_name\t: " + str(sqlite_file_name))
    
    with mozidb.IndexedDB(sqlite_file_name) as conn:
        print("[*] Proxy Status\t: " + IDBObjectWrapper(conn).read_object('iconActive'))

        ts = IDBObjectWrapper(conn).read_object('dateConnected')
        if(ts != None):
            print('[!] caution -> There is no timestamp for VPN-stop, so the VPN_HISTORY includes all of the history after VPN-start')
            c_code = IDBObjectWrapper(conn).read_object('proxyCountry')
            one_data = [1, int(ts), 1999999999, c_code]
            insert_one(con, tuple(one_data))
            
            print("[*] result DB dumped")
            return True

        else:
            print('[!] caution -> There is no timestamp, so the VPN_HISTORY can\'t be made')
            print("[*] result DB dumped")
            return False

def chrome_browsec(args,con):
    print("[*] args \t\t: " + str(args))
    
    log_file_name = [x for x in pathlib.Path(args.dbpath).glob("*.log")][0]
    print("[*] log_file_name\t: " + str(log_file_name))
    with open(log_file_name, encoding='utf-8', errors='ignore') as f:
        logs = f.read()
        idx=logs.rfind('Request servers list #0 started')
        id_num = 1
        VPN_ON=False
        one_data = [1, 0, 1999999999, 'null']
        while(1):
            idx = idx + logs[idx:].find('Store: PAC update.')
            idx = idx + logs[idx:].find('New')
            ct_idx = logs[idx:].find('country')
            ct = logs[idx+ct_idx+12:idx+ct_idx+14]
            mode_idx = logs[idx+ct_idx:].find('mode')
            mode = logs[idx+ct_idx+mode_idx+9:idx+ct_idx+mode_idx+14]

            ts_idx = logs[idx:].find('timestamp')
            ts = logs[idx+ts_idx+11:idx+ts_idx+22]
            ts = ts[0]+ts[2:]

            idx = idx + logs[idx:].find('Store: low leverl PAC update.')
            idx = idx + logs[idx:].find(ct)
            port_idx = logs[idx:].find(':443')
            url = logs[idx+14:idx+port_idx]

            if(VPN_ON == False):
                one_data = [id_num, int(ts), 1999999999, url]
                VPN_ON = True
            else:
                one_data[2] = int(ts)
                insert_one(con, tuple(one_data))
                id_num = id_num+1
                VPN_ON = False
                if(mode=='proxy'):
                    one_data = [id_num, int(ts), 1999999999, url]
                    VPN_ON = True
                
            logs = logs[idx+1:]
            idx=logs.find('Store: PAC update.')
            if(idx==-1):
                break

    print("[*] result DB dumped")

def firefox_browsec(args, con):
    print("[*] args \t\t: " + str(args))
    sqlite_file_name = [x for x in pathlib.Path(args.dbpath).glob("*.sqlite")][-1]
    print("[*] sqlite_file_name\t: " + str(sqlite_file_name))

    with mozidb.IndexedDB(sqlite_file_name) as conn:
        logs=str(IDBObjectWrapper(conn).read_object('log'))

        idx=logs.rfind('Request servers list #0 started')
        id_num = 1
        VPN_ON=False
        one_data = [1, 0, 1999999999, 'null']
        while(1):
            idx = idx + logs[idx:].find('Store: PAC update.')
            idx = idx + logs[idx:].find('New')
            ct_idx = logs[idx:].find('country')
            ct = logs[idx+ct_idx+10:idx+ct_idx+12]
            mode_idx = logs[idx:].find('mode')
            mode = logs[idx+mode_idx+7:idx+mode_idx+12]
            
            ts_idx = logs[idx:].find('timestamp')
            ts = logs[idx+ts_idx+12:idx+ts_idx+22]

            idx = idx + logs[idx:].find('Store: low leverl PAC update.')
            idx = idx + logs[idx:].find(ct)
            port_idx = logs[idx:].find(':443')
            url = logs[idx+12:idx+port_idx]

            if(VPN_ON == False):
                one_data = [id_num, int(ts), 1999999999, url]
                VPN_ON = True
            else:
                one_data[2] = int(ts)
                insert_one(con, tuple(one_data))
                id_num = id_num+1
                VPN_ON = False
                if(mode=='proxy'):
                    one_data = [id_num, int(ts), 1999999999, url]
                    VPN_ON = True
                
            logs = logs[idx+1:]
            idx=logs.find('Store: PAC update.')
            if(idx==-1):
                break
    
    print("[*] result DB dumped")

if __name__ == "__main__":
    sys.exit(main())
