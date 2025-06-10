import random
import string
from datetime import datetime, timedelta

# --- Configurações ---
random.seed(42)
start_date = datetime(2025, 1, 1)
end_date = datetime(2025, 7, 31)

# Mínimos garantidos + incremento aleatório
n_voos_por_dia = random.randint(5, 10)           # pelo menos 5
n_avioes = random.randint(10, 20)                # pelo menos 10
n_modelos_distintos = 5                          # fixo
n_aeroportos = 12                                # fixo
n_bilhetes = random.randint(30000, 35000)        # pelo menos 30000


output = open("populate.sql", "w")
def print_sql(line):
    output.write(line + "\n")


# --- Dados reais e exemplo ---
modelos_aviao = ["Airbus A320", "Boeing 737", "Airbus A330", "Boeing 787", "Embraer 190"]
aeroportos = [
    ("LIS", "Humberto Delgado", "Lisboa", "Portugal"),
    ("OPO", "Francisco Sá Carneiro", "Porto", "Portugal"),
    ("ORY", "Orly", "Paris", "França"),
    ("CDG", "Charles de Gaulle", "Paris", "França"),
    ("MAD", "Adolfo Suárez-Barajas", "Madrid", "Espanha"),
    ("BCN", "El Prat", "Barcelona", "Espanha"),
    ("LHR", "Heathrow", "Londres", "Reino Unido"),
    ("LGW", "Gatwick", "Londres", "Reino Unido"),
    ("FCO", "Fiumicino", "Roma", "Itália"),
    ("MXP", "Malpensa", "Milão", "Itália"),
    ("BUD", "Ferenc Liszt", "Budapeste", "Hungria"),
    ("MUC", "Franz Josef Strauss", "Munique", "Alemanha"),
]

# --- Geradores auxiliares ---
def random_serie():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

def random_nome():
    return ''.join(random.choices(string.ascii_letters + ' ', k=random.randint(6, 12))).title()

# --- 1. Aeroportos ---
for cod, nome, cidade, pais in aeroportos:
    print(f"INSERT INTO aeroporto VALUES ('{cod}', '{nome}', '{cidade}', '{pais}');")

# --- 2. Aviões e Assentos ---
avioes = []
for i in range(n_avioes):
    modelo = random.choice(modelos_aviao)
    no_serie = random_serie()
    avioes.append((no_serie, modelo))
    print(f"INSERT INTO aviao VALUES ('{no_serie}', '{modelo}');")
    
    filas = 30  # 30 filas por avião
    for f in range(1, filas + 1):
        for c in "ABCDEF":
            lugar = f"{f}{c}"
            prim = f <= 3  # Primeiras 3 filas = 1ª classe
            print(f"INSERT INTO assento VALUES ('{lugar}', '{no_serie}', {str(prim).upper()});")

# --- 3. Voos ---
voos = []
current_time = start_date
voo_id = 1

while current_time <= end_date:
    for _ in range(n_voos_por_dia):
        partida, chegada = random.sample(aeroportos, 2)
        partida_cod, chegada_cod = partida[0], chegada[0]
        hora_partida = datetime.combine(current_time.date(), datetime.min.time()) + timedelta(hours=random.randint(5, 20))
        duracao_voo = timedelta(hours=random.randint(1, 4))
        hora_chegada = hora_partida + duracao_voo
        aviao = random.choice(avioes)[0]

        print(f"INSERT INTO voo VALUES ({voo_id}, '{aviao}', '{hora_partida}', '{hora_chegada}', '{partida_cod}', '{chegada_cod}');")
        voos.append((voo_id, aviao))
        voo_id += 1

        # Voo de regresso
        hora_partida2 = hora_chegada + timedelta(hours=1)
        hora_chegada2 = hora_partida2 + duracao_voo
        print(f"INSERT INTO voo VALUES ({voo_id}, '{aviao}', '{hora_partida2}', '{hora_chegada2}', '{chegada_cod}', '{partida_cod}');")
        voos.append((voo_id, aviao))
        voo_id += 1
    current_time += timedelta(days=1)

# --- 4. Vendas e Bilhetes ---
for venda_id in range(1, int(n_bilhetes / 1.5) + 1):
    nif = ''.join(random.choices(string.digits, k=9))
    balcao = random.choice(aeroportos)[0]
    hora = start_date + timedelta(days=random.randint(0, (end_date - start_date).days))
    print(f"INSERT INTO venda VALUES ({venda_id}, '{nif}', '{balcao}', '{hora}');")

# --- 5. Bilhetes ---
for i in range(1, n_bilhetes + 1):
    voo, aviao = random.choice(voos)
    venda_id = random.randint(1, int(n_bilhetes / 1.5))
    nome = random_nome()
    preco = round(random.uniform(50, 500), 2)
    prim = random.random() < 0.2
    fila = random.randint(1, 3 if prim else 30)
    assento = f"{fila}{random.choice('ABCDEF')}"
    print(f"INSERT INTO bilhete (voo_id, codigo_reserva, nome_passegeiro, preco, prim_classe, lugar, no_serie) "
          f"VALUES ({voo}, {venda_id}, '{nome}', {preco}, {str(prim).upper()}, '{assento}', '{aviao}');")

