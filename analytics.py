import ipaddress
from collections import Counter
import pandas as pd

"""# ==========================================
# 1. WCZYTANIE I CZYSZCZENIE DANYCH
# ==========================================
"""

# Wczytanie pliku źródłowego
df = pd.read_csv("bank_transactions.csv")

# Znalezienie uszkodzonych wierszy
uszkodzone_wiersze = df[["user_id", "amount"]].isna().any(axis=1)

uszkodzone_id = df[uszkodzone_wiersze]["transaction_id"]

# Zapis uszkodzonych identyfikatorów do pliku
pd.DataFrame(uszkodzone_id, columns=["transaction_id"]).to_csv("missing_report.csv", index=False)

# Usunięcie uszkodzonych wierszy i stworzenie czystej kopii danych
df_clean = df.dropna(subset=["amount", "user_id"]).copy()

"""# ===========================================
# 2. DETEKCJA ANOMALII I OSZUSTW
# ===========================================
"""

# Definicja podsieci prywatnych (lokalnych)
zakresy_prywatne = [
    ipaddress.IPv4Network("10.0.0.0/8"),
    ipaddress.IPv4Network("172.16.0.0/12"),
    ipaddress.IPv4Network("192.168.0.0/16"),
]

def czy_adres_prywatny(adres_ip):
    try:
        adres_ip = ipaddress.IPv4Address(adres_ip)
        for zakres in zakresy_prywatne:
            if adres_ip in zakres:
                return True
        return False
    except ipaddress.AddressValueError:
        return False

# Filtrowanie: Kwota powyżej 15 000 oraz adres ip Nie jest adresem prywatnym
podejrzane_wiersze = df_clean[
    (df_clean["amount"] > 15000) & (~df_clean["ip_address"].apply(czy_adres_prywatny))
]

# Zapis podejrzanych rekordów do pliku alertu
pd.DataFrame(podejrzane_wiersze).to_csv("fraud_alert.csv", index=False)

"""# =============================================
# 3. AGREGACJA DANYCH
# =============================================
"""

# Konwersja na date bez czasu i stworzenie kolumny Rok-miesiąc
df_clean["timestamp"] = pd.to_datetime(df_clean["timestamp"])
df_clean["month"] = df_clean["timestamp"].dt.to_period("M").astype(str)

# Grupowanie z obliczeniami sumy, średniej, ilości
df_grouped = df_clean.groupby(["category", "month"], as_index=False).agg(
    amount_sum=('amount', 'sum'),
    amount_mean=('amount', 'mean'),
    amount_count=('amount', 'count')
)

# Zaokrąglanie wartości średniej do 2 miejsc po przecinku
df_grouped["amount_mean"] = df_grouped["amount_mean"].round(2)

# Zapis gotowego raportu miesięcznego
df_grouped.to_csv("monthly_report.csv", index=False)

graphic = """
 {o,o}
 /)  )            PANDAS DATA LAB
---"-"---         Wszystkie statystyki policzone!
 __|||__          Pliki gotowe do wysylki.
"""
print(graphic)
