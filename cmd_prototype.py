# cmd_prototype.py  (Full Smart Version + optional fingerprint integration)
import os
import json
import speech_recognition as sr
import pyttsx3
from datetime import datetime
import requests
import numpy as np

# face libs (optional)
try:
    import cv2
    import face_recognition
    FACE_LIBS_AVAILABLE = True
except Exception as e:
    # print("Face libs not available:", e)
    FACE_LIBS_AVAILABLE = False

# ---------- Try fingerprint SDK imports (optional) ----------
FINGERPRINT_AVAILABLE = False
# Try common fingerprint Python wrappers - add more as you get device & SDK
try:
    import pyuareu  # example for DigitalPersona (if you have)
    FINGERPRINT_AVAILABLE = True
    FINGERPRINT_BACKEND = "pyuareu"
except Exception:
    try:
        import pyfingerprint  # example for some optical sensors
        FINGERPRINT_AVAILABLE = True
        FINGERPRINT_BACKEND = "pyfingerprint"
    except Exception:
        FINGERPRINT_BACKEND = None
        FINGERPRINT_AVAILABLE = False

# ---------- Voice Engine ----------
engine = pyttsx3.init()
engine.setProperty('rate', 160)
voices = engine.getProperty('voices')
if voices:
    engine.setProperty('voice', voices[0].id)

def speak(text):
    print("🔊 Jarvish:", text)
    try:
        engine.say(text)
        engine.runAndWait()
    except Exception:
        pass

def listen():
    r = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            print("🎙 Listening...")
            r.adjust_for_ambient_noise(source, duration=0.5)
            audio = r.listen(source, phrase_time_limit=6)
        text = r.recognize_google(audio, language="hi-IN")
        print("🗣 You said:", text)
        return text
    except Exception:
        return ""

# ---------- Data ----------
DATA_FILE = "customers.json"
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        customers = json.load(f)
else:
    customers = {}

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(customers, f, indent=2, ensure_ascii=False)

# ---------- Item Prices (11 default items) ----------
item_prices = {
    "Maggi": 15,
    "Biscuit": 10,
    "Sugar": 50,   # per kg default
    "Bread": 20,
    "Rice": 40,    # per kg
    "Dal": 120,    # per kg
    "Oil": 180,    # per litre
    "Salt": 20,    # per kg
    "Tea": 200,    # per kg
    "Milk": 60,    # per litre
    "Egg": 6       # per piece
}

# ---------- SMS (Fast2SMS) ----------
FAST2SMS_API = "https://www.fast2sms.com/dev/bulkV2"
API_KEY = "YOUR_FAST2SMS_API_KEY"  # replace

def send_due_message(name, phone, due):
    message = f"Namaste {name}, aapka baki paisa {due} rupaye hai. Kripya time se jama karein."
    payload = {
        "authorization": API_KEY,
        "route": "dlt",
        "sender_id": "FSTSMS",
        "message": message,
        "numbers": phone,
        "flash": 0
    }
    try:
        r = requests.get(FAST2SMS_API, params=payload, timeout=10)
        print("Fast2SMS response:", r.status_code, r.text)
    except Exception as e:
        print("SMS send error:", e)

# ---------- Face helpers ----------
FACES_DIR = "faces"
if not os.path.exists(FACES_DIR):
    os.makedirs(FACES_DIR, exist_ok=True)

def register_face(name):
    if not FACE_LIBS_AVAILABLE:
        speak("Face recognition libraries installed nahi hain.")
        return False
    speak(f"{name}, camera open ho rahi hai. Please look at the camera and hold still.")
    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        speak("Camera open nahi hui. Check webcam.")
        return False
    encoding = None
    start = datetime.now()
    while (datetime.now() - start).seconds < 12:
        ret, frame = cam.read()
        if not ret: continue
        small = cv2.resize(frame, (0,0), fx=0.5, fy=0.5)
        rgb = small[:, :, ::-1]
        locs = face_recognition.face_locations(rgb)
        encs = face_recognition.face_encodings(rgb, locs)
        if encs:
            encoding = encs[0].tolist()
            cv2.imwrite(os.path.join(FACES_DIR, f"{name.replace(' ','_')}.jpg"), frame)
            break
        cv2.imshow("Register - press q to cancel", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cam.release()
    cv2.destroyAllWindows()
    if not encoding:
        speak("Face detect nahi hua. Try in better light.")
        return False
    if name not in customers:
        customers[name] = {"phone":"","address":"","notes":"","photo":"","transactions":[], "face_encoding": encoding, "quick_code": None}
    else:
        customers[name]["face_encoding"] = encoding
    save_data()
    speak(f"Face registered and saved for {name}.")
    return True

def open_by_face(match_threshold=0.55):
    if not FACE_LIBS_AVAILABLE:
        speak("Face recognition libraries installed nahi hain.")
        return None
    known_names = []
    known_encodings = []
    for name, data in customers.items():
        enc = data.get("face_encoding")
        if enc:
            known_names.append(name)
            known_encodings.append(enc)
    if not known_encodings:
        speak("Koi registered face nahi mila.")
        return None
    speak("Scanning... Camera on. Please look at camera.")
    cam = cv2.VideoCapture(0)
    matched_name = None
    start = datetime.now()
    while (datetime.now() - start).seconds < 10:
        ret, frame = cam.read()
        if not ret: continue
        small = cv2.resize(frame, (0,0), fx=0.25, fy=0.25)
        rgb = small[:, :, ::-1]
        locs = face_recognition.face_locations(rgb)
        encs = face_recognition.face_encodings(rgb, locs)
        for face_enc in encs:
            distances = face_recognition.face_distance([np.array(e) for e in known_encodings], face_enc)
            best_idx = int(np.argmin(distances))
            best_dist = float(distances[best_idx])
            if best_dist <= match_threshold:
                matched_name = known_names[best_idx]
                break
        if matched_name: break
        cv2.imshow("Scanning - press q to cancel", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cam.release()
    cv2.destroyAllWindows()
    if matched_name:
        speak(f"{matched_name} se match hua.")
        return matched_name
    else:
        speak("Kisi registered customer se match nahi hua.")
        return None

# ---------- Fingerprint skeleton (with vendor hooks) ----------
# NOTE: To fully enable, install vendor SDK and Python wrapper, then implement these functions
def register_fingerprint(name):
    """Register fingerprint template for 'name' using vendor SDK (placeholder)."""
    if not FINGERPRINT_AVAILABLE:
        speak("Fingerprint SDK/device available nahi hai. Configure SDK first.")
        return False
    # Example pseudo-flow (replace with real SDK calls)
    try:
        if FINGERPRINT_BACKEND == "pyuareu":
            # implement DigitalPersona registration using pyuareu sample code
            # save template as bytes in customers[name]['fingerprint_template']
            pass
        elif FINGERPRINT_BACKEND == "pyfingerprint":
            # implement sensor enrolment
            pass
        # When done:
        # customers[name]['fingerprint_template'] = <template_bytes_base64>
        save_data()
        speak("Fingerprint registered (placeholder).")
        return True
    except Exception as e:
        speak("Fingerprint register failed: " + str(e))
        return False

def match_fingerprint():
    """Capture fingerprint and compare with stored templates. Return matched name or None."""
    if not FINGERPRINT_AVAILABLE:
        return None
    try:
        # PSEUDO: capture template from sensor, compare with stored templates
        # for name, data in customers.items():
        #    if compare_templates(captured, data['fingerprint_template']): return name
        return None
    except Exception:
        return None

# ---------- Quick-code ----------
def make_quick_code_from_phone(phone):
    digits = ''.join(ch for ch in phone if ch.isdigit())
    return digits[-4:] if len(digits) >= 4 else digits

def ensure_unique_quick_code(base):
    existing = {d.get("quick_code") for d in customers.values()}
    if base not in existing: return base
    i = 1
    while True:
        candidate = f"{base}_{i}"
        if candidate not in existing: return candidate
        i += 1

def assign_quick_code_for_customer(name, phone):
    base = make_quick_code_from_phone(phone)
    code = ensure_unique_quick_code(base)
    if name not in customers:
        customers[name] = {"phone":phone,"address":"","notes":"","photo":"","transactions":[], "face_encoding": None, "fingerprint_template": None, "quick_code": code}
    else:
        customers[name]["phone"] = phone
        customers[name]["quick_code"] = code
    save_data()
    return code

def find_names_by_quick_code(code_input):
    code_norm = code_input.strip().lower()
    return [n for n,d in customers.items() if (d.get("quick_code") or "").strip().lower() == code_norm]

# ---------- Dues helpers ----------
def calculate_total_due(name):
    return sum(t.get("due",0) for t in customers.get(name, {}).get("transactions", []))

def clear_due(name):
    total_due = calculate_total_due(name)
    if total_due <= 0:
        speak("Koi baki paisa nahi hai.")
        return False
    tx = {
        "date": datetime.now().strftime("%d-%m-%Y %H:%M"),
        "items": "Due Clearance",
        "paid": total_due,
        "due": 0
    }
    customers[name]["transactions"].append(tx)
    save_data()
    speak(f"Due clear ho gaya: {total_due} rupaye ka record add kar diya.")
    return True

# ---------- Profile Menu ----------
def parse_qty_str(qty_str):
    # remove non-numeric except dot
    num = ''.join(ch for ch in qty_str if (ch.isdigit() or ch == '.'))
    return float(num) if num else None

def profile_menu(name):
    while True:
        total_due = calculate_total_due(name)
        speak(f"{name} ka current total due: {total_due} rupaye.")
        print(f"\n--- {name} Profile Menu ---")
        print("1. Add transaction (naya saman + payment)")
        print("2. Clear due (ek click me baki clear hona, record banaega)")
        print("3. Register / Update face")
        print("4. Register / Update fingerprint (if device configured)")
        print("5. Show full history")
        print("6. Back to main menu")
        choice = input("Choose (1-6) or speak: ").strip() or listen()
        choice = (choice or "").strip().lower()
        if choice in ("1","add","add transaction"):
            speak("Items aur quantity bolo. Format: Item Qty Item Qty ... PaidAmount")
            item_text = input("Items (press Enter to speak): ").strip() or listen()
            parts = item_text.split()
            try:
                paid = float(parts[-1])
            except:
                speak("Paid amount galat hai. Cancel kar raha hoon.")
                continue
            items_parts = parts[:-1]
            total = 0; item_summary = []; ok = True
            for i in range(0, len(items_parts), 2):
                try:
                    item = items_parts[i].capitalize()
                    qty_str = items_parts[i+1]
                    qty = parse_qty_str(qty_str)
                    if qty is None: raise ValueError("qty parse fail")
                    priceper = item_prices.get(item, 15)
                    amt = priceper * qty
                    total += amt
                    item_summary.append(f"{item} x{qty} = {amt}")
                except Exception:
                    ok = False
                    break
            if not ok or not item_summary:
                speak("Item format galat hai. Example: Maggi 2 Biscuit 1 50")
                continue
            due = total - paid
            tx = {"date": datetime.now().strftime("%d-%m-%Y %H:%M"),
                  "items": ", ".join(item_summary),
                  "paid": paid,
                  "due": due}
            customers[name]["transactions"].append(tx)
            save_data()
            speak(f"Transaction saved for {name}. Total {total}, Paid {paid}, Due {due}.")
            if due > 0:
                send_due_message(name, customers[name].get("phone",""))
        elif choice in ("2","clear","clear due","due clear"):
            ok = clear_due(name)
            if ok:
                phone = customers[name].get("phone","")
                if phone:
                    send_due_message(name, phone, 0)
        elif choice in ("3","register face","face"):
            register_face(name)
        elif choice in ("4","register fingerprint","fingerprint"):
            if not FINGERPRINT_AVAILABLE:
                speak("Fingerprint SDK/device not configured. See README to enable.")
            else:
                register_fingerprint(name)
        elif choice in ("5","history","show"):
            print(json.dumps(customers[name], indent=2, ensure_ascii=False))
        elif choice in ("6","back","b"):
            break
        else:
            speak("Invalid choice. Dobara try karo.")

# ---------- Commands mapping ----------
commands = {
    "view": ["view","dikha","dekha","view profile","viewprofile"],
    "add": ["add","transaction","add transaction","daala"],
    "exit": ["exit","quit","band","niklo"],
    "register_face": ["register_face","face register"],
    "open_by_face": ["open_by_face","scan face","scanface"],
    "send_dues": ["send_dues","due sms","notify dues"],
    "open_code": ["opencode","code","open code","quick code"],
    "register_fingerprint": ["register_fingerprint","fingerprint register"]
}

def match_command(text):
    text = (text or "").lower()
    for cmd,kws in commands.items():
        for kw in kws:
            if kw in text: return cmd
    return None

# ---------- Main Loop ----------
speak("Namaste! Jarvish AI Khata Book Full Smart Version me swagat hai.")
speak("Aap text likh ke ya bol kar dono se kaam kar sakte hain.")

while True:
    speak("Kya karna hai? View profile, add transaction, register_face, open_by_face, open_code, send_dues, fingerprint, ya exit?")
    cmd = input("Input (press Enter to speak): ").strip() or listen()
    action = match_command(cmd)

    if action == "exit":
        speak("Theek hai, data save kar raha hoon. Bye.")
        save_data()
        break

    elif action == "view":
        speak("Kiska profile dekhna hai? (name / quick-code / phone last4)")
        name = input("Customer name (press Enter to speak): ").strip() or listen()
        name = (name or "").strip()
        if name.isdigit() and 3 < len(name) <= 6:
            matches = find_names_by_quick_code(name)
            if matches:
                selected = matches[0]
                speak(f"{selected} ka profile open kar raha hoon.")
                print(json.dumps(customers[selected], indent=2, ensure_ascii=False))
                profile_menu(selected)
                continue
        name = name.capitalize()
        if name in customers:
            speak(f"{name} ka profile. Phone {customers[name].get('phone','nahi')}, address {customers[name].get('address','nahi')}.")
            print(json.dumps(customers[name], indent=2, ensure_ascii=False))
            profile_menu(name)
        else:
            speak(f"{name} ka record nahi mila.")

    elif action == "add":
        speak("Customer ka naam bolo ya likho:")
        name = input("Customer name (press Enter to speak): ").strip() or listen()
        name = (name or "").strip().capitalize()
        if not name:
            speak("Naam nahi mila.")
            continue
        if name not in customers:
            speak(f"{name} naya customer, profile banate hain.")
            phone = input("Phone: ").strip()
            address = input("Address: ").strip()
            notes = input("Notes (optional): ").strip()
            qcode = assign_quick_code_for_customer(name, phone)
            speak(f"Short quick code set hua: {qcode}")
            customers[name] = {"phone":phone,"address":address,"notes":notes,"photo":"","transactions":[], "face_encoding": None, "fingerprint_template": None, "quick_code": qcode}
            save_data()
        else:
            speak(f"{name} pehle se maujood hai.")
        profile_menu(name)

    elif action == "register_face":
        speak("Customer ka naam bolo for face registration:")
        name = input("Customer name (press Enter to speak): ").strip() or listen()
        name = (name or "").strip().capitalize()
        if name in customers:
            register_face(name)
        else:
            speak("Profile nahi mila. Pehle transaction add karo to create profile.")

    elif action == "open_by_face":
        matched = open_by_face()
        if matched:
            speak(f"{matched} ka profile open kar raha hoon.")
            print(json.dumps(customers.get(matched,{}), indent=2, ensure_ascii=False))
            profile_menu(matched)

    elif action == "open_code":
        speak("Code bolo ya likh do (phone ke last 4 digits ya assigned quick code):")
        code_input = input("Code (press Enter to speak): ").strip() or listen()
        if code_input:
            open_profile_by_quick_code_flow(code_input)

    elif action == "send_dues":
        speak("Sab customers ko due reminders bhej raha hoon...")
        for name, data in customers.items():
            total_due = sum(t.get("due",0) for t in data.get("transactions",[]))
            if total_due > 0 and data.get("phone"):
                send_due_message(name, data["phone"], total_due)
        speak("Done.")

    elif action == "register_fingerprint":
        speak("Customer ka naam bolo for fingerprint registration:")
        name = input("Customer name (press Enter to speak): ").strip() or listen()
        name = (name or "").strip().capitalize()
        if name in customers:
            register_fingerprint(name)
        else:
            speak("Profile nahi mila. Pehle add karo.")

    else:
        raw = (cmd or "").strip()
        if raw.isdigit() and (3 < len(raw) <= 6):
            matches = find_names_by_quick_code(raw)
            if matches:
                name = matches[0]
                speak(f"{name} ka profile open.")
                print(json.dumps(customers[name], indent=2, ensure_ascii=False))
                profile_menu(name)
            else:
                speak("Kisi ka profile is code se match nahi hua.")
        else:
            speak("Command samajh nahi aaya. Dobara try karo ya type 'help'.")
            

# end
# cd C:\Users\ASUS\Desktop\JarvishProject
#python cmd_prototype.py