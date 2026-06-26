CANCER_BIOMARKERS = [
    {"index": 1, "key": "CEA", "name": "CEA", "label": "1 CEA"},
    {"index": 2, "key": "NSE", "name": "NSE", "label": "2 NSE"},
    {"index": 3, "key": "Cyfra21-1", "name": "Cyfra21-1", "label": "3 Cyfra21-1"},
    {"index": 4, "key": "ProGPR", "name": "ProGPR", "label": "4 ProGPR"},
    {"index": 5, "key": "SCCA", "name": "SCCA", "label": "5 SCCA"},
    {"index": 6, "key": "P53", "name": "P53", "label": "6 P53"},
    {"index": 7, "key": "CA125", "name": "CA125", "label": "7 CA125"},
    {"index": 8, "key": "TSGF", "name": "TSGF", "label": "8 TSGF"},
    {"index": 9, "key": "GAGE 7", "name": "GAGE 7", "label": "9 GAGE 7"},
    {"index": 10, "key": "MAGE A1", "name": "MAGE A1", "label": "10 MAGE A1"},
]


def get_biomarker_by_key(key):
    for biomarker in CANCER_BIOMARKERS:
        if biomarker["key"] == key:
            return dict(biomarker)
    return dict(CANCER_BIOMARKERS[0])
