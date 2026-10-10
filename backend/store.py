"""
store.py - MongoDB persistence for TheLogWatch.

Collections
  events         every classified log line (auto-deleted after EVENT_TTL_DAYS)
  devices        one document per device: counts, worst verdict, first/last seen
  known_devices  hardware IDs the router has already seen (so "new device" survives restarts)
  ai_cache       AI answers keyed by a hash of the logs they were asked about

Uses the synchronous PyMongo driver; the web app calls it through asyncio.to_thread.
Set MONGODB_URI=mongomock:// to run without a database (tests / quick demos).
"""
from datetime import datetime, timezone

from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.errors import OperationFailure

PUBLIC = {"_id": 0, "created": 0}


class Store:
    def __init__(self, uri, db_name="logwatch", ttl_days=14):
        if uri.startswith("mongomock://"):
            import mongomock
            client = mongomock.MongoClient()
            self.memory = True
        else:
            kw = {"serverSelectionTimeoutMS": 10000, "appname": "logwatch"}
            if uri.startswith("mongodb+srv://") or "tls=true" in uri.lower():
                import certifi
                kw["tlsCAFile"] = certifi.where()
            client = MongoClient(uri, **kw)
            self.memory = False
        self.client = client
        db = client[db_name]
        self.events = db.events
        self.devices = db.devices
        self.known = db.known_devices
        self.ai = db.ai_cache
        self.ttl_days = ttl_days

    # ------------------------------------------------------------------ setup
    def init(self):
        try:
            self.events.create_index([("rx", DESCENDING)])
            self.events.create_index([("device", ASCENDING), ("rx", DESCENDING)])
            self.events.create_index([("scenario", ASCENDING)])
            self.events.create_index([("rx", DESCENDING), ("id", DESCENDING)])
            self.events.create_index([("device", ASCENDING), ("rx", DESCENDING), ("id", DESCENDING)])
            if self.ttl_days > 0:
                self.events.create_index("created", expireAfterSeconds=int(self.ttl_days * 86400))
            self.known.create_index([("device", ASCENDING), ("mac", ASCENDING)], unique=True)
            self.ai.create_index("created", expireAfterSeconds=7 * 86400)
        except OperationFailure as e:
            # Atlas users without createIndex (e.g. a read-only role) can still run the app,
            # just without the indexes and the automatic TTL cleanup.
            print(f"WARNING: could not create MongoDB indexes ({e.details.get('errmsg', e)}). "
                  "Give the database user the readWrite role on this database.")

    def ping(self):
        if self.memory:
            return True
        self.client.admin.command("ping")
        return True

    # ------------------------------------------------------------------ writes
    def insert_events(self, docs):
        if not docs:
            return
        now = datetime.now(timezone.utc)
        self.events.insert_many([{**d, "created": now} for d in docs])
        ops = {}
        for d in docs:
            o = ops.setdefault(d["device"], {"count": 0, "alerts": 0, "worst": 0, "last": 0,
                                              "first": d["rx"], "source": d["source"]})
            o["count"] += 1
            o["alerts"] += int(d["level"] >= 2)
            o["worst"] = max(o["worst"], d["level"])
            o["last"] = max(o["last"], d["rx"])
        for name, o in ops.items():          # a handful of devices per batch, so one update each is fine
            self.devices.update_one(
                {"_id": name},
                {"$inc": {"count": o["count"], "alerts": o["alerts"]},
                 "$max": {"worst": o["worst"], "last": o["last"]},
                 "$setOnInsert": {"name": name, "source": o["source"], "first": o["first"]}},
                upsert=True)

    def add_known(self, device, mac):
        self.known.update_one({"device": device, "mac": mac}, {"$setOnInsert": {"device": device, "mac": mac}}, upsert=True)

    def reset(self):
        self.events.delete_many({})
        self.devices.delete_many({})
        self.known.delete_many({})

    # ------------------------------------------------------------------ reads
    def recent(self, limit=400, device=None, scenario=None):
        q = {}
        if device:
            q["device"] = device
        if scenario:
            q["scenario"] = scenario
        rows = list(self.events.find(q, PUBLIC).sort("rx", DESCENDING).limit(limit))
        rows.reverse()
        return rows

    def all_events(self, limit=20000):
        return list(self.events.find({}, PUBLIC).sort("rx", ASCENDING).limit(limit))

    def history(self, limit=250, device=None, source=None, alerts=False, before=None):
        q = {}
        if device:
            q["device"] = device
        if source:
            q["source"] = source
        if alerts:
            q["level"] = {"$gte": 2}
        if before:
            rx, event_id = before
            q["$or"] = [{"rx": {"$lt": rx}}, {"rx": rx, "id": {"$lt": event_id}}]
        rows = list(self.events.find(q, PUBLIC).sort([("rx", DESCENDING), ("id", DESCENDING)]).limit(limit + 1))
        more = len(rows) > limit
        rows = rows[:limit]
        cursor = [rows[-1]["rx"], rows[-1]["id"]] if more else None
        return {"events": rows, "next": cursor}

    def device_list(self):
        return list(self.devices.find({}, {"_id": 0}).sort("last", DESCENDING).limit(200))

    def counts(self):
        out = {}
        for r in self.events.aggregate([{"$group": {"_id": "$level", "n": {"$sum": 1}}}]):
            out[str(r["_id"])] = r["n"]
        return out

    def known_all(self):
        return [(k["device"], k["mac"]) for k in self.known.find({}, {"_id": 0})]

    def ai_get(self, key):
        doc = self.ai.find_one({"_id": key})
        return doc["text"] if doc else None

    def ai_put(self, key, text):
        self.ai.update_one({"_id": key}, {"$set": {"text": text, "created": datetime.now(timezone.utc)}}, upsert=True)
