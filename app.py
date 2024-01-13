#!/usr/bin/python

from flask import Flask, render_template, request, jsonify
import os, random, requests, hashlib, dotenv

app = Flask(__name__)

LANGUAGES = set([
  "en", #English
  "ar", #Arabic
  "az", #Azerbaijani
  "zh", #Chinese
  "cs", #Czech
  "nl", #Dutch
  "fi", #Finnish
  "fr", #French
  "de", #German
  "hi", #Hindi
  "hu", #Hungarian
  "id", #Indonesian
  "ga", #Irish
  "it", #Italian
  "ja", #Japanese
  "ko", #Korean
  "pl", #Polish
  "pt", #Portuguese
  "ru", #Russian
  "es", #Spanish
  "sv", #Swedish
  "tr", #Turkish
  "uk", #Ukranian
  "vi", #Vietnamese
  ])

dotenv.load_dotenv()
TL_END = os.getenv('TL_END') #endpoint for cloud translation API
TS_END = os.getenv('TS_END') #endpoint for cloud transcription API

# route for "/" (frontend):
@app.route('/')
def index():
  return render_template("index.html")

# play a game of translation telephone using the source field of the POST data as a starting point
@app.route('/telephone', methods=["POST"])
def telephone_endpoint():
  langs = ["en"] + random.sample(LANGUAGES,3) + ["en"]
  s = request.form["source"]
  for i in range(1,len(langs)):
    s = translate(s, langs[i-1], langs[i], TL_END)
  return jsonify({"telephone" : s,})

# transcribe an audio file submitted through POST data
@app.route('/transcribe', methods=["POST"])
def transcribe_endpoint():
  if (not (file := request.files['audio'] or file.filename.endswith(".wav"))):
      return "No audio file selected", 500
  if os.path.isfile(fin := "tmp.wav"):
    os.remove(fin)
  file.save(fin)
  ts = transcribe(fin, TS_END)
  if ts is None:
    return "Transcription Error", 500
  return {"transcription" : ts}, 200

# hash a file using md5 and return md5 checksum
def hashFile(fname):
  with open(fname, "rb") as f:
    return hashlib.md5(f.read()).hexdigest()

# hash a string using md5 and return md5 checksum
def hashString(string):
  return hashlib.md5(string.encode('utf-8')).hexdigest()

# translate a string s from language src to language dest, returning from cache if possible and caching if not
translate_cache = {}
def translate(s, src, dest, endpoint):
  print(src)
  if src in LANGUAGES and dest in LANGUAGES:
    my_json = {'q': s, 'source': src, 'target': dest, 'format': 'text'}
    my_key = s+src+dest
    if my_key in translate_cache:
      return translate_cache[my_key]
    else:
      r = requests.post(url = endpoint, json = my_json)
      if int(r.status_code) != 200:
        translate_cache[my_key] = None
        return None
      else:
        translated_data = r.json()
        if 'translatedText' not in translated_data or translated_data['translatedText'] == '':
          translate_cache[my_key] = None
          return None
        else:
          translate_cache[my_key] = translated_data['translatedText']
          return translated_data['translatedText']
  else:
    return None

# translate an english audio file af to text, returning from cache if possible and caching if not
transcribe_cache = {}
def transcribe(fin, endpoint):
  if len(fin) < 4 or fin[-4:] != '.wav':
    return None
  else:
    my_headers = {'Content-Type':'application/octet-stream'}
    if fin in transcribe_cache:
      return transcribe_cache[fin]
    else:
      if os.path.exists(fin):
        file = open(fin, 'rb')
        contents = file.read()
        r = requests.post(url = endpoint, data = contents, headers = my_headers)
        if int(r.status_code) != 200:
          transcribe_cache[fin] = None
          return None
        else:
          to_return = str(r.text)
          if to_return == '':
            transcribe_cache[fin] = None
            return None
          else:
            transcribe_cache[fin] = to_return
            return to_return
      else:
        transcribe_cache[fin] = None
        return None
  
