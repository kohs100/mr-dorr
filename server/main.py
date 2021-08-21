from flask import Flask, abort, request, jsonify
from flask_cors import CORS
import json
import atexit
import re
import time

DB_REFRI = {}
DB_DRINK = {}
DB_AUTHK = {}

PATTERN_SID = re.compile(r'^[A-F0-9]{8}$')


def load_db():
    global DB_REFRI
    global DB_DRINK
    global DB_AUTHK
    try:
        with open('key.json', 'r') as f:
            DB_AUTHK = json.load(f)
    except:
        print('key.json not found. Exiting...')
        exit()
    try:
        with open('refrig.json', 'r') as f:
            DB_REFRI = json.load(f)
    except Exception as e:
        print('refrig.json not found. Creating one...')
    try:
        with open('drinks.json', 'r') as f:
            DB_DRINK = json.load(f)
    except Exception as e:
        print('drinks.json not found. Creating one...')


def save_db():
    with open('refrig.json', 'w') as f:
        json.dump(DB_REFRI, f)
    with open('drinks.json', 'w') as f:
        json.dump(DB_DRINK, f)


app = Flask(__name__)
CORS(app)


def validate_hb(data):
    if "opened" not in data or "status" not in data:
        return False

    try:
        for sid, obj in data['status'].items():
            if not PATTERN_SID.search(sid):
                print('invalid sector id')
                return False

            if len(obj["status"]) != obj["numslot"]:
                print('slot number mismatch')
                return False

            if obj["mainslot"] < 0 or obj["mainslot"] >= obj["numslot"]:
                print('invalid mainslot number')
                return False
    except Exception as e:
        print('validate_hb: exception occured:', e)
        return False

    return True


@app.route('/refrig/<rid>', methods=['POST'])
def ep_refrig(rid):
    global DB_REFRI

    if rid not in DB_REFRI:
        print('ep_refrig: keyError:', rid)
        abort(404)

    try:
        data = json.loads(request.data)
    except json.decoder.JSONDecodeError:
        print('ep_refrig: JSONDecodeError')
        abort(400)

    if not validate_hb(data):
        print('ep_refrig: Invalid HeartBeat')
        abort(400)
    
    DB_REFRI[rid]["initialized"] = True
    DB_REFRI[rid]["opened"] = data["opened"]
    DB_REFRI[rid]["status"] = data["status"]
    DB_REFRI[rid]["last_updated"] = time.time_ns()

    resp = {}
    resp["urgent"] = DB_REFRI[rid]["urgent"]
    resp["status"] = {}
    
    for sid, mslot in DB_REFRI[rid]["request"].items():
        if sid in data["status"]:
            if data["status"][sid]["mainslot"] != mslot:
                resp["status"][sid] = mslot
        else:
            print("ep_refrig: invalid sector id request")
    DB_REFRI[rid]["request"] = {}
    
    return jsonify(resp)

@app.route('/stat', methods=['GET'])
def ep_stat_list():
    resp = {}
    for rid in DB_REFRI:
        resp[rid] = DB_REFRI[rid]["name"]
    
    return jsonify(resp)

@app.route('/stat/<rid>', methods=['GET'])
def ep_stat_get(rid):
    if rid not in DB_REFRI:
        print('ep_stat_get: keyError:', rid)
        abort(404)
    obj = DB_REFRI[rid]
    resp = {}
    resp["name"] = obj["name"]
    resp["initialized"] = obj["initialized"]
    if not obj["initialized"]:
        return jsonify(resp)
    else:
        resp["opened"] = obj["opened"]
        resp["status"] = obj["status"]
        resp["lastUpdated"] = obj["last_updated"]
        return jsonify(resp)

@app.route('/stat/<rid>', methods=['POST'])
def ep_stat_create(rid):
    global DB_REFRI
    try:
        data = json.loads(request.data)
    except json.decoder.JSONDecodeError:
        print('ep_stat_create: JSONDecodeError')
        abort(400)
    
    try:
        if 'name' not in data:
            print('ep_stat_create: Invalid body: no name')
            abort(400)
        if rid not in DB_REFRI:
            print('ep_stat_create: Creating new refrigerator', rid)
            DB_REFRI[rid] = {
                "name": data['name'],
                "initialized": False,
                "request": {},
                "urgent": False
            }
        else:
            print('ep_stat_create: modifying name of refrigerator', rid)
            DB_REFRI[rid]['name'] = data['name']
    except Exception as e:
        print('ep_stat_create: Invalid body')
        abort(400)
    
    return ''

@app.route('/stat/<rid>', methods=['PUT'])
def ep_stat_update(rid):
    global DB_REFRI
    try:
        data = json.loads(request.data)
    except json.decoder.JSONDecodeError:
        print('ep_stat_update: JSONDecodeError')
        abort(400)
    
    if rid not in DB_REFRI:
        print('ep_stat_update: KeyError:', rid)
        abort(404)
    
    if not DB_REFRI[rid]['initialized']:
        return 'Uninitialized RID', 404

    try:
        for sid in data['status']:
            if sid not in DB_REFRI[rid]['status']:
                print('ep_stat_update: invalid sector id:', sid)
                abort(400)

        for sid, mslot in data['status'].items():
            DB_REFRI[rid]['request'][sid] = mslot
    except Exception as e:
        print('ep_stat_update: exception occured: ', e)
        abort(500)
    
    return 'Request Pushed for '+rid, 200

@app.route('/stat/<rid>', methods=['DELETE'])
def ep_stat_delete(rid):
    global DB_REFRI
    if rid not in DB_REFRI:
        print('ep_stat_delete: KeyError:', rid)
        abort(404)
    DB_REFRI.pop(rid)

    return ''

@app.before_request
def auth_request():
    xkey = request.headers.get('x-api-key')

    if not xkey:
        abort(401)              # 401 Unauthorized
    if xkey not in DB_AUTHK:
        abort(403)              # 403 Forbidden
    

if __name__ == '__main__':
    load_db()
    atexit.register(save_db)
    app.run()
