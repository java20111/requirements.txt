import os, json, hmac, hashlib, time
from datetime import datetime, timezone
from urllib.parse import parse_qsl
from functools import wraps
from flask import Flask, request, jsonify, send_from_directory
from pymongo import MongoClient, ReturnDocument
from dotenv import load_dotenv

load_dotenv()
BASE = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, static_folder='static', template_folder='templates')
BOT_TOKEN = os.getenv('BOT_TOKEN', '8929285063:AAEnVYs_71Z9xiB7w1l8HR19AG-FrcJ3JAc')
DEV_MODE = os.getenv('DEV_MODE', 'false').lower() == 'true'
MONGO_URI = os.getenv('MONGO_URI', 'mongodb+srv://<db_username>:oi1cI4t8w60vAjvB@cluster0.mrgssy9.mongodb.net/?appName=Cluster0')
DB_NAME = os.getenv('MONGO_DB', 'city_builder')

if MONGO_URI:
    mongo = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = mongo[DB_NAME]
    users = db.users
else:
    mongo = None
    db = None
    users = None

CATALOG = {
    'small_house': {'name':'Small House','price':100,'income':2,'population':5,'xp':20,'size':[2,2],'min_level':1,'kind':'house'},
    'apartment': {'name':'Apartment','price':700,'income':14,'population':50,'xp':90,'size':[3,3],'min_level':2,'kind':'apartment'},
    'shop': {'name':'Shop','price':1000,'income':15,'population':4,'xp':120,'size':[3,2],'min_level':2,'kind':'shop'},
    'school': {'name':'School','price':2500,'income':20,'population':0,'xp':260,'size':[4,3],'min_level':4,'kind':'school'},
    'factory': {'name':'Factory','price':5000,'income':100,'population':10,'xp':450,'size':[4,4],'min_level':5,'kind':'factory'},
    'hospital': {'name':'Hospital','price':10000,'income':80,'population':0,'xp':800,'size':[4,4],'min_level':8,'kind':'hospital'},
    'business_center': {'name':'Business Center','price':50000,'income':1000,'population':100,'xp':2500,'size':[5,5],'min_level':10,'kind':'business'},
    'park': {'name':'Park','price':300,'income':0,'population':0,'xp':45,'size':[3,3],'min_level':1,'kind':'park'},
    'road': {'name':'Road','price':50,'income':0,'population':0,'xp':5,'size':[2,2],'min_level':1,'kind':'road'}
}

def now(): return datetime.now(timezone.utc)

def level_for_xp(xp):
    level = 1
    need = 100
    while xp >= need and level < 50:
        level += 1
        need += level * 100
    return level

def validate_init_data(init_data):
    if not init_data:
        if DEV_MODE: return {'id': 1, 'first_name': 'Developer', 'username': 'developer'}
        return None
    if not BOT_TOKEN: return None
    pairs = dict(parse_qsl(init_data, keep_blank_values=True))
    received = pairs.pop('hash', None)
    auth_date = int(pairs.get('auth_date', '0'))
    if not received or time.time() - auth_date > 86400: return None
    check = '\n'.join(f'{k}={pairs[k]}' for k in sorted(pairs))
    secret = hmac.new(b'WebAppData', BOT_TOKEN.encode(), hashlib.sha256).digest()
    expected = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, received): return None
    try: return json.loads(pairs['user'])
    except (KeyError, json.JSONDecodeError): return None

def current_user():
    return validate_init_data(request.headers.get('X-Telegram-Init-Data', ''))

def require_user(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        tg = current_user()
        if not tg: return jsonify({'error':'Telegram authentication failed'}), 401
        if users is None: return jsonify({'error':'MONGO_URI is not configured'}), 500
        uid = int(tg['id'])
        user = users.find_one({'_id':uid})
        if not user:
            user = {'_id':uid,'first_name':tg.get('first_name','Player'),'last_name':tg.get('last_name',''),'username':tg.get('username',''),'coins':1000,'xp':0,'level':1,'city_name':'New City','buildings':[],'unlocked_zones':1,'last_income':now()}
            users.insert_one(user)
        return fn(user, *args, **kwargs)
    return wrapped

def serialize(user):
    buildings=[]; income=0; population=0; value=0
    for b in user.get('buildings',[]):
        c=CATALOG.get(b['type']);
        if not c: continue
        mult=1 + (b.get('level',1)-1)*0.6
        income += int(c['income']*mult); population += int(c['population']*mult); value += int(c['price']*mult)
        buildings.append({**b,'name':c['name'],'kind':c['kind']})
    xp=user.get('xp',0); level=max(user.get('level',1), level_for_xp(xp))
    return {'id':user['_id'],'name':user.get('first_name','Player'),'username':user.get('username',''),'coins':int(user.get('coins',0)),'xp':xp,'level':level,'city_name':user.get('city_name','New City'),'income':income,'population':population,'city_value':value,'buildings':buildings,'catalog':CATALOG,'unlocked_zones':user.get('unlocked_zones',1)}

@app.get('/')
def index(): return send_from_directory('templates','index.html')
@app.get('/static/<path:path>')
def static_files(path): return send_from_directory('static',path)

@app.get('/api/state')
@require_user
def state(user): return jsonify(serialize(user))

@app.post('/api/build')
@require_user
def build(user):
    data=request.get_json(silent=True) or {}; typ=data.get('type'); x=int(data.get('x',0)); z=int(data.get('z',0))
    c=CATALOG.get(typ)
    if not c: return jsonify({'error':'Unknown building'}),400
    if user.get('level',1) < c['min_level']: return jsonify({'error':'City level is too low'}),400
    if user.get('coins',0) < c['price']: return jsonify({'error':'Not enough coins'}),400
    if not (0 <= x < 24 and 0 <= z < 24): return jsonify({'error':'Invalid position'}),400
    for b in user.get('buildings',[]):
        if abs(b['x']-x) < c['size'][0] and abs(b['z']-z) < c['size'][1]: return jsonify({'error':'This area is occupied'}),400
    new={'id':f'{int(time.time()*1000)}','type':typ,'x':x,'z':z,'level':1,'created_at':now().isoformat()}
    xp=user.get('xp',0)+c['xp']; new_level=level_for_xp(xp)
    updated=users.find_one_and_update({'_id':user['_id']},{'$inc':{'coins':-c['price'],'xp':c['xp']},'$set':{'level':new_level},'$push':{'buildings':new}},return_document=ReturnDocument.AFTER)
    return jsonify(serialize(updated))

@app.post('/api/upgrade')
@require_user
def upgrade(user):
    data=request.get_json(silent=True) or {}; bid=str(data.get('id'))
    buildings=user.get('buildings',[]); target=next((b for b in buildings if b['id']==bid),None)
    if not target: return jsonify({'error':'Building not found'}),404
    c=CATALOG[target['type']]; old=target.get('level',1); price=int(c['price']*(old+1)*0.8); xp=int(c['xp']*0.5)
    if user.get('coins',0)<price: return jsonify({'error':'Not enough coins'}),400
    updated=users.find_one_and_update({'_id':user['_id'],'buildings.id':bid},{'$inc':{'coins':-price,'xp':xp,'buildings.$.level':1},'$set':{'level':level_for_xp(user.get('xp',0)+xp)}},return_document=ReturnDocument.AFTER)
    return jsonify(serialize(updated))

@app.post('/api/collect')
@require_user
def collect(user):
    last=user.get('last_income') or now(); elapsed=max(0,(now()-last).total_seconds()); minutes=min(elapsed/60, 720); amount=int(serialize(user)['income']*minutes)
    updated=users.find_one_and_update({'_id':user['_id']},{'$inc':{'coins':amount},'$set':{'last_income':now()}},return_document=ReturnDocument.AFTER)
    return jsonify({'collected':amount,'state':serialize(updated)})

@app.post('/api/city-name')
@require_user
def city_name(user):
    name=str((request.get_json(silent=True) or {}).get('name','')).strip()[:32]
    if len(name)<2: return jsonify({'error':'Name is too short'}),400
    updated=users.find_one_and_update({'_id':user['_id']},{'$set':{'city_name':name}},return_document=ReturnDocument.AFTER)
    return jsonify(serialize(updated))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT','5000')), debug=DEV_MODE)
