from json.decoder import JSONDecodeError
from flask import Flask, abort, request, jsonify
from flask_cors import CORS
from schema import Schema
import json
import atexit
import re
import time
import jsonschema

DB_REFRI = {}
DB_DRINK = {}
DB_AUTHK = {}


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


@app.route('/refrig/<rid>', methods=['POST'])
def ep_refrig(rid):
    global DB_REFRI

    if rid not in DB_REFRI:
        print('ep_refrig: keyError:', rid)
        abort(404)

    try:
        data = json.loads(request.data)
        jsonschema.validate(schema=Schema.ep_refrig_post, instance=data)
    except json.decoder.JSONDecodeError:
        print('ep_refrig: JSONDecodeError')
        abort(400)
    except jsonschema.ValidationError as e:
        print('ep_refrig: Bad HeartBeat:', e)
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
        jsonschema.validate(schema=Schema.ep_stat_create, instance=data)
    except json.decoder.JSONDecodeError:
        print('ep_stat_create: JSONDecodeError')
        abort(400)
    except jsonschema.ValidationError as e:
        print('ep_stat_create: Bad HeartBeat:', e)
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

    return ''


@app.route('/stat/<rid>', methods=['PUT'])
def ep_stat_update(rid):
    global DB_REFRI
    try:
        data = json.loads(request.data)
        jsonschema.validate(schema=Schema.ep_stat_update, instance=data)
    except json.decoder.JSONDecodeError:
        print('ep_stat_update: JSONDecodeError')
        abort(400)
    except jsonschema.ValidationError as e:
        print('ep_stat_update: Bad HeartBeat:', e)
        abort(400)

    if rid not in DB_REFRI:
        print('ep_stat_update: KeyError:', rid)
        abort(404)

    if not DB_REFRI[rid]['initialized']:
        return 'Uninitialized RID', 404

    for sid, mslot in data['status'].items():
        if sid not in DB_REFRI[rid]['status']:
            print('ep_stat_update: invalid sector id:', sid)
            abort(400)
        if mslot >= DB_REFRI[rid]['status']['numslot']:
            print('ep_stat_update: request mainslot out of range')
            abort(400)

    for sid, mslot in data['status'].items():
        DB_REFRI[rid]['request'][sid] = mslot

    return 'Request Pushed for ' + rid, 200


@app.route('/stat/<rid>', methods=['DELETE'])
def ep_stat_delete(rid):
    global DB_REFRI
    if rid not in DB_REFRI:
        print('ep_stat_delete: KeyError:', rid)
        abort(404)
    DB_REFRI.pop(rid)

    return ''


@app.route('/db', methods=['GET'])
def ep_db_list():
    global DB_DRINK
    return jsonify(DB_DRINK)


@app.route('/db/<did>', methods=['GET'])
def ep_db_get(did):
    if did in DB_DRINK:
        return jsonify(DB_DRINK[did])
    else:
        abort(404)


@app.route('/db/<did>', methods=['POST'])
def ep_db_create(did):
    global DB_DRINK

    try:
        data = json.loads(request.data)
        jsonschema.validate(schema=Schema.ep_db_create, instance=data)
    except json.decoder.JSONDecodeError:
        print('ep_db_create: JSONDecodeError')
        abort(400)
    except jsonschema.ValidationError as e:
        print('ep_db_create: Bad HeartBeat:', e)
        abort(400)

    if did in DB_DRINK:
        DB_DRINK[did]['name'] = data['name']
    else:
        DB_DRINK[did] = {
            'name': data['name'],
            'img': False
        }
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
