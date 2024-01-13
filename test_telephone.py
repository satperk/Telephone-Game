from app import *
from datetime import datetime, timedelta
import os, time, requests, base64, pytest, sys, shutil, uuid
import dotenv

phrases = [
    ["hello","en","es","Hola."],
    ["hello","en","pt","Olá."],
    ["squirrel","en","de","Eichhörnchen"],
    ["squirrel","en","vi","Con sóc"],
    ["good morning","en","ja","おはようございます"],
    ["good morning","en","fr","Bonjour."],
    ["telephone","en","zh","电话"],
    ["telephone","en","ga","teileafón"],

    ["skrzypce","pl","en","violin"],
    ["valp","sv","en","puppy"],
    ["शुभ प्रभात","hi","en","Good Morning"],
    ["könyvtár","hu","en","Library"],
    ]

audio = [
    ("asparagus"   ,"YSBzcGlyaXQgb2Ygc2FsYWQgY29vayB0aGUgYXNwYXJhZ3VzIGluIHNhbHRlZCB3YXRlciBkcmFpbiBhbmQgY2hpbGw="),
    ("disadvantage","b25lIHdobyB3cml0ZXMgb2Ygc3VjaCBhbiBlcmEgbGFib3VycyB1bmRlciBhIHRyb3VibGVzb21lIGRpc2FkdmFudGFnZQ=="),
    ("flower"      ,"aW5kZWVkIG5vdCBhIGZsb3dlciBlc2NhcGVkIGhpcyBtaXNjaGlldm91cyBzdWdnZXN0aW9ucw=="),
    ("staircase"   ,"YnV0IGluIGxlc3MgdGhhbiBmaXZlIG1pbnV0ZXMgdGhlIHN0YWlyY2FzZSBncm9hbmVkIGJlbmVhdGggYW4gZXh0cmFvcmRpbmFyeSB3ZWlnaHQ="),
    ("travel"      ,"aSBiZWdhbiB0byBlbmpveSB0aGUgZXhoaWxhcmF0aW5nIGRlbGlnaHQgb2YgdHJhdmVsbGluZyBhIGxpZmUgb2YgZGVzaXJlIGdyYXRpZmljYXRpb24gYW5kIGxpYmVydHk="),
    ]
randomaudio = random.choice(audio)

@pytest.fixture(autouse=True, scope='session')
def pytest_sessionstart():
    global TL_END, TS_END
    dotenv.load_dotenv()
    TL_END = os.getenv('TL_END')
    TS_END = os.getenv('TS_END')

def test_translation_from_english():
    for p in phrases[:-4]:
        assert(translate(*p[:3],TL_END) == p[3]), \
            f"Translation of {p[0]} from {p[1]} to {p[2]} failed"

def test_translation_to_english():
    for p in phrases[-4:]:
        assert(translate(*p[:3],TL_END) == p[3]), \
            f"Translation of {p[0]} from {p[1]} to {p[2]} failed"

def test_translation_cache():
    for p in phrases:
        translate(*p[:3],TL_END)

    now = datetime.now()
    for p in phrases:
        assert(translate(*p[:3],TL_END) == p[3]), \
            f"Translation of {p[0]} failed"
    walltime = (datetime.now() - now)
    us       = walltime.seconds*1000000 + walltime.microseconds
    assert(us < 1000), \
        f"Lookup for cached translations took too long ({us}us < 1000us)"

def test_translation_invalid():
    for p in phrases:
        assert (translate(p[0],p[1],"notalanguage",TL_END) is None), \
            f"Translation to non-existent language succeeded"

        assert (translate(p[0],"notalanguage",p[2],TL_END) is None), \
            f"Translation from non-existent language succeeded"

        assert (translate("",p[1],p[2],TL_END) is None), \
            f"Translation of empty string succeeded"

def test_transcription_normal():
    for a in audio:
        assert(os.path.exists(os.path.join("test-audio",a[0]+".wav"))), \
            f"test-audio/{a[0]}.wav is missing"

    a,t = randomaudio
    af  = os.path.join("test-audio",a+".wav")

    afcopy = str(uuid.uuid4())+".wav"
    shutil.copy(af,afcopy)
    try:
        ts = transcribe(afcopy,TS_END)
    finally:
        os.remove(afcopy)

    same = base64.b64encode(ts.encode("ascii")).decode("ascii") == t
    assert(same), \
        f"Transcription of {af} did not return expected result"

def test_transcription_cache():
    a,t = randomaudio
    af  = os.path.join("test-audio",a+".wav")
    transcribe(af,TS_END)

    afcopy = str(uuid.uuid4())+".wav"
    shutil.copy(af,afcopy)
    try:
        ts = transcribe(afcopy,TS_END)
    finally:
        os.remove(afcopy)

    now = datetime.now()
    same = base64.b64encode(ts.encode("ascii")).decode("ascii") == t
    assert(same), \
        f"Transcription of {af} did not return expected result"
    walltime = (datetime.now() - now)
    us       = walltime.seconds*1000000 + walltime.microseconds
    assert(us < 100000), \
        f"Lookup for cached transcription of {af} took too long ({us}us < 100000us)"

def test_transcription_invalid():
    assert (transcribe("test_telephone.py",TS_END) is None), \
        f"Transcription succeeded for non-audio file"

    assert (transcribe("thisisnotarealaudiofile.wav",TS_END) is None), \
        f"Transcription succeeded for invalid file"
