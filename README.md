# Jarvish AI Khata Book (CMD Prototype)

## Project Type
AI-Based Smart Khata / Ledger System for Small Shops

## Core Idea
Jarvish AI Khata Book is a voice-enabled, AI-assisted digital ledger system designed for small shopkeepers and rural businesses.  
It helps them manage customer entries, udhaar (credit), and dues using voice commands, quick access codes, face login, and SMS reminders.

---

## Key Features (Based on This Prototype)

### 1. Voice + Text Based Khata Operation
- Shopkeeper can operate the system using **voice (Hindi)** or **manual text input**.
- Uses `speech_recognition` and `pyttsx3` for:
  - Taking voice commands
  - Speaking back responses (Jarvish voice assistant)

### 2. Smart Customer Profiles with Quick Codes
- Each customer has:
  - Name, phone, address, notes
  - Transactions history
  - Optional face encoding
  - Auto-generated **quick code** (usually from phone last 4 digits)
- Shopkeeper can open profile using:
  - Name  
  - Quick-code  
  - Phone digits

### 3. Intelligent Transaction & Due Management
- Supports item-wise billing with default kirana items (Maggi, Biscuit, Sugar, Rice, Dal, Oil, Milk, etc.).
- Automatically:
  - Calculates total amount
  - Stores paid + due
  - Updates customer due balance
- Stores all transactions in `customers.json` for persistence.

### 4. Automatic Due Reminder via SMS (Fast2SMS)
- Integrates with **Fast2SMS API**.
- Sends an SMS like:
  > "Namaste {name}, aapka baki paisa {due} rupaye hai. Kripya time se jama karein."
- Can trigger bulk due reminders for all customers with pending amounts.

### 5. Face-Based Customer Identification (Optional)
- If `opencv` and `face_recognition` libraries are installed:
  - Customer’s face can be registered using webcam.
  - Later, shopkeeper can use **face scan to open the correct customer profile**.
- Uses:
  - Face encoding storage in JSON
  - Saved images in `faces/` folder

### 6. Fingerprint Integration Ready (Future Hook)
- Placeholder functions for fingerprint registration and matching:
  - `register_fingerprint(name)`
  - `match_fingerprint()`
- Designed to support future integration with fingerprint SDKs (e.g. pyuareu, pyfingerprint).

### 7. Profile Menu (Full Smart Control)
For each customer profile:
- Add new transaction (items + paid + due)
- Clear all due with a single operation (creates a record entry)
- Register/update face
- Register/update fingerprint (when device is configured)
- Show full transaction history (JSON dump)

---

## Tech Stack

- **Language:** Python
- **Voice I/O:** speech_recognition, pyttsx3
- **Face Recognition (optional):** OpenCV, face_recognition, NumPy
- **Storage:** JSON (`customers.json`)
- **SMS Integration:** Fast2SMS API

---

## Ownership Notice
This project idea, flow and implementation prototype is originally created and owned by:

**Name:** Nawneet Pandey  
**Created On:** 21 Nov 2025  

This repository contains the original Jarvish AI Khata Book concept and prototype code.
