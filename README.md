
# Policy Violation Checker

This project analyzes **text conversations** and **images** to detect policy violations based on a predefined rules document.

## 📌 Features
- ✅ **Text-based policy analysis** (`data_classifier.py`): Checks conversations for rule violations.
- ✅ **Image-based policy analysis** (`image_classifier.py`): Detects rule violations in images.
- ✅ **Integration with OpenAI Assistants**: Uses GPT-based models for analysis.
- ✅ **Logging & Result Storage**: Saves analyzed results for reference.

---

## 🛠️ **Setup Instructions**

### **1️⃣ Prerequisites**
- Install **Python 3.8+**
- Get an **OpenAI API Key** from [OpenAI](https://platform.openai.com/)
- Install dependencies:

```bash
pip install -r requirements.txt
```

---

### **2️⃣ Configure Environment**
Set up your OpenAI API key as an **environment variable**:

```bash
export OPENAI_API_KEY="" <-- talk to me
```
(For Windows: `set OPENAI_API_KEY=`)

---

## 🚀 **Running the Scripts**
### **🔹 Run Text Policy Checker**
Checks text conversations (`chat_chains.json`) against the rule file (`tos.txt`).

```bash
python data_classifier.py
```
**Output:** Results saved in `results_dict.txt`.

---

### **🔹 Run Image Policy Checker**
Checks images against the rule file (`tos.txt`).

```bash
python image_classifier.py
```
**Output:** Results saved in `image_results_dict.txt`.

---

## 📝 **File Structure**
```
📂 project-folder
 ├── data_classifier.py        # Text-based policy analysis
 ├── image_classifier.py       # Image-based policy analysis
 ├── requirements.txt          # Python dependencies
 ├── results_dict.txt          # Output for text analysis
 ├── image_results_dict.txt    # Output for image analysis
 ├── chat_chains.json          # Sample chat conversations
 ├── tos.txt                   # Rules document for analysis
 ├── README.md                 # Project documentation
```

---

## 📌 **How It Works**
1. **Uploads the rules document (`tos.txt`)** to OpenAI Assistants.
2. **Processes conversations/images** and compares them to the rules.
3. **Identifies potential violations** and categorizes them as:
   - ✅ **No Violation**
   - ⚠️ **Potential Violation**
   - ❌ **Clear Violation**
4. **Logs and saves results** for review.

---

## 🛠 **Customization**
- Modify `tos.txt` to change rule definitions.
- Add more images in `image_classifier.py` (update `image_urls` list).
- Adjust OpenAI model settings in `Config`.

---

## 📌 **Contributing**
Feel free to fork this repository and submit pull requests!

---

## 📧 **Contact**
For any questions, email **danaplus@gmail.com**.

---

## Personal Note

thank you for getting that far in my README note.
I had a great time doing this project, thanks for the tip about Claude (:
