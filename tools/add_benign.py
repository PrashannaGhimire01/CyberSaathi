import csv, os

DATASET = "data/dataset.csv"

# 48 casual, everyday benign messages: (text, language)
benign = [
    # English
    ("Hi, are you coming to dinner tonight?", "en"),
    ("Happy birthday! Hope you have a wonderful day.", "en"),
    ("Let's meet at the coffee shop around 5pm.", "en"),
    ("Can you pick up some vegetables on your way home?", "en"),
    ("Thank you so much for your help yesterday, I really appreciate it.", "en"),
    ("The movie was great, we should watch the next one together.", "en"),
    ("I'll be a little late, the traffic is heavy today.", "en"),
    ("Good morning! Did you sleep well?", "en"),
    ("Congratulations on your new job, so happy for you!", "en"),
    ("Don't forget we have the family lunch on Saturday.", "en"),
    ("I miss you, let's catch up soon.", "en"),
    ("Call me when you get home safely.", "en"),
    # Romanized Nepali
    ("Khana khaisakyau? Ma aja ghar chittai aauchu.", "roman"),
    ("Aja office kasto bhayo? Thakai lagyo hola.", "roman"),
    ("Bholi bihana ko plan k cha? Ghumna jane?", "roman"),
    ("Didi, aama lai sanchai cha bhanera sodhnu la.", "roman"),
    ("Dhanyabad hai, timro maya sadhai yaad aauchha.", "roman"),
    ("Ma market janchhu, kehi chahiyo bhane bhana.", "roman"),
    ("Aja mausam ramro cha, ghumna jaam na.", "roman"),
    ("Timro janmadin ko subhakamana! Khusi raha.", "roman"),
    ("Bhai, ghar aaipugyau ki nai? Message gara.", "roman"),
    ("Bholi college jane ho? Sathai jaam.", "roman"),
    ("Chiya khana aau na, gaff garchhau.", "roman"),
    ("Maya, chittai bhetaula hai.", "roman"),
    # Nepali (Devanagari)
    ("आज साँझ खाना खान आउँछौ?", "ne"),
    ("जन्मदिनको शुभकामना! खुसी रहनुहोस्।", "ne"),
    ("भोलि बिहान भेटौं है।", "ne"),
    ("आमालाई सन्चै छ भनेर सोध्नू।", "ne"),
    ("धेरै धन्यवाद, तिम्रो सहयोग सम्झिरहन्छु।", "ne"),
    ("आज मौसम राम्रो छ, घुम्न जाऔं।", "ne"),
    ("घर सुरक्षित पुगेपछि फोन गर्नू।", "ne"),
    ("भोलि परिवारसँग खाना खाने कार्यक्रम छ, नबिर्सनू।", "ne"),
    ("तिमीलाई सम्झिरहेको छु, चाँडै भेटौं।", "ne"),
    ("काम सकियो? थकाइ लाग्यो होला।", "ne"),
    ("बजार जाँदैछु, केही चाहिन्छ भने भन।", "ne"),
    ("राम्रोसँग सुत्यौ? शुभ प्रभात।", "ne"),
    # Mixed
    ("Aja office ma meeting thyo, ali late hunchha ghar aauna.", "mixed"),
    ("Happy anniversary! तिमीहरूलाई धेरै माया।", "mixed"),
    ("Weekend ma ghumna jane plan cha, तिमी free छौ?", "mixed"),
    ("Thanks yaar, तिम्रो help le dherai farak paryo.", "mixed"),
    ("Dinner ready cha, chittai ghar aau na।", "mixed"),
    ("Congrats on your result! धेरै खुसी लाग्यो।", "mixed"),
    ("Good night, राम्रोसँग सुत्नू। Bholi bhetaula.", "mixed"),
    ("Movie ticket book garisake, साँझ ७ बजे हो।", "mixed"),
    ("Aama le khana pakaunu bho, chittai aau।", "mixed"),
    ("Meeting postpone bhayo, aja ma free chu.", "mixed"),
    ("Take care hai, ghar pugera message gara।", "mixed"),
    ("Kaam sakiyo, aba ghar farkidai chu, दिनको खाना सँगै खाऔं।", "mixed"),
]

with open(DATASET, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    rows = list(reader)
max_id = max(int(r['id']) for r in rows)

# make sure the file ends with a newline before we append
with open(DATASET, 'rb') as f:
    f.seek(-1, os.SEEK_END)
    need_newline = f.read(1) != b'\n'

sources = ["sms", "viber", "whatsapp", "messenger"]
with open(DATASET, 'a', newline='', encoding='utf-8') as f:
    if need_newline:
        f.write('\n')
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    for i, (text, lang) in enumerate(benign):
        writer.writerow({
            'id': max_id + 1 + i,
            'text': text,
            'label': 'legit',
            'category': 'personal',
            'language': lang,
            'source': sources[i % len(sources)],
            'date_added': '2026-09-30',
        })

print(f"Added {len(benign)} benign messages. New total: {len(rows) + len(benign)}")