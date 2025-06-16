import random
import string
from datetime import datetime, timedelta

# --- Configurações ---
random.seed(42)
start_date = datetime(2025, 1, 1)
end_date = datetime(2025, 7, 31)

n_voos_por_dia = random.randint(5, 15)
n_avioes = random.randint(10, 20)
n_modelos_distintos =  random.randint(5, 11)
n_aeroportos = 12
n_bilhetes = random.randint(30000, 40000)

output = open("populate.sql", "w")
def print_sql(line=""):
    output.write(line + "\n")

# --- Dados base ---
modelos_aviao = ["Airbus A320", "Boeing 737", "Airbus A330", "Boeing 787", "Embraer 190", "Boeing 777", "Airbus A350", "Boeing 747", "Airbus A380", "Bombardier CRJ900", "ATR 72"]
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


nomes = [
    "João Silva", "Maria Santos", "Pedro Costa", "Ana Pereira", "Luís Oliveira",
    "Carla Martins", "Rui Gomes", "Sofia Ferreira", "Tiago Rocha", "Inês Almeida",
    "Paulo Nunes", "Cláudia Dias", "Ricardo Pinto", "Sara Cardoso", "André Sousa",
    "Marta Teixeira", "Filipe Moreira", "Helena Ramos", "Bruno Carvalho", "Catarina Mendes", 
    "Vasco Azevedo", "Joana Pires", "Hugo Correia", "Raquel Silva", "Diogo Martins",
    "Patrícia Costa", "Gonçalo Lima", "Teresa Rocha", "Miguel Araújo", "Lúcia Ferreira",
    "Nuno Barros", "Mariana Cunha", "Sérgio Alves", "Filipa Monteiro", "Ricardo Reis",
    "Ana Rita", "João Pedro", "Mónica Silva", "Carlos Mendes", "Sílvia Costa",
    "Tiago Martins", "Isabel Pereira", "Rafael Gomes", "Beatriz Santos", "Eduardo Nunes",
    "Cátia Dias", "Alexandre Pinto", "Liliana Cardoso", "Gustavo Teixeira", "Patrícia Sousa",
    "Bruno Rocha", "Sara Almeida", "Ricardo Moreira", "Ana Paula", "João Paulo",
    "Marta Silva", "Fábio Costa", "Cláudia Pereira", "Rui Martins", "Sofia Nunes",
    "Tiago Ferreira", "Inês Gomes", "Paulo Rocha", "Carla Alves", "Luís Teixeira",
    "Ana Costa", "Pedro Martins", "Maria Pereira", "João Nunes", "Sofia Silva",
    "Ricardo Costa", "Cláudia Gomes", "Filipe Rocha", "Helena Martins", "Bruno Nunes",
    "Catarina Pereira", "Vasco Silva", "Joana Costa", "Hugo Martins", "Raquel Gomes",
    "Diogo Rocha", "Patrícia Alves", "Gonçalo Teixeira", "Teresa Nunes", "Miguel Silva",
    "Lúcia Costa", "Nuno Martins", "Mariana Pereira", "Sérgio Gomes", "Filipa Rocha"]


# --- Auxiliares ---
def random_serie():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

def random_nome():
    return ''.join(random.choices(string.ascii_letters + ' ', k=random.randint(6, 12))).title()

# --- 1. Aeroportos ---
print_sql("-- === 1. Aeroportos ===")
for cod, nome, cidade, pais in aeroportos:
    print_sql(f"INSERT INTO aeroporto (codigo, nome, cidade, pais) VALUES ('{cod}', '{nome}', '{cidade}', '{pais}');")
print_sql()

# --- 2. Aviões ---
avioes = []
print_sql("-- === 2. Aviões ===")
for _ in range(n_avioes):
    modelo = random.choice(modelos_aviao)
    no_serie = random_serie()
    avioes.append((no_serie, modelo))
    print_sql(f"INSERT INTO aviao (no_serie, modelo) VALUES ('{no_serie}', '{modelo}');")
print_sql()

# --- 3. Assentos ---
print_sql("-- === 3. Assentos ===")
for no_serie, _ in avioes:
    for f in range(1, 31):  # 30 filas
        for c in "ABCDEF":
            lugar = f"{f}{c}"
            prim = f <= 3
            print_sql(f"INSERT INTO assento (lugar, no_serie, prim_classe) VALUES ('{lugar}', '{no_serie}', {str(prim).upper()});")
print_sql()

# --- 4. Voos ---
print_sql("-- === 4. Voos ===")
voos = []
current_time = start_date
voo_id = 1
used_voos = set()  # To ensure (no_serie, hora_partida) is unique
used_chegada = set()  # To ensure (hora_chegada, partida, chegada) is unique
used_partida_combo = set()  # To ensure (hora_partida, partida, chegada) is unique

# Map airport code to city for quick lookup
aeroporto_cidade = {a[0]: a[2] for a in aeroportos}

# Para cada avião, manter o aeroporto atual
aviao_estado = {}
for no_serie, _ in avioes:
    aviao_estado[no_serie] = random.choice(aeroportos)[0]

voos_ida = set()  # (origem, destino, data)
voos_volta_necessarios = set()  # (destino, origem, data)

while current_time <= end_date:
    voos_dia = []
    voos_gerados_hoje = 0
    # Garante pelo menos 5 voos por dia
    n_voos_hoje = max(n_voos_por_dia, 5)
    for _ in range(n_voos_hoje):
        # Escolher avião e respetivo aeroporto atual
        no_serie = random.choice(list(aviao_estado.keys()))
        origem = aviao_estado[no_serie]
        origem_cidade = aeroporto_cidade[origem]
        # Escolher destino diferente da origem e de cidade diferente
        destinos_possiveis = [a[0] for a in aeroportos if a[0] != origem and aeroporto_cidade[a[0]] != origem_cidade]
        if not destinos_possiveis:
            continue
        destino = random.choice(destinos_possiveis)

        hora_partida = datetime.combine(current_time.date(), datetime.min.time()) + timedelta(hours=random.randint(5, 20))
        duracao = timedelta(hours=random.randint(1, 4))
        hora_chegada = hora_partida + duracao

        # Garantir unicidade
        tentativas = 0
        while (
            (no_serie, hora_partida) in used_voos or
            (no_serie, hora_chegada) in used_voos or
            (hora_chegada, origem, destino) in used_chegada or
            (hora_partida, origem, destino) in used_partida_combo
        ):
            hora_partida = datetime.combine(current_time.date(), datetime.min.time()) + timedelta(hours=random.randint(5, 20))
            duracao = timedelta(hours=random.randint(1, 4))
            hora_chegada = hora_partida + duracao
            tentativas += 1
            if tentativas > 20:
                break  # Evita loop infinito

        if tentativas > 20:
            continue

        used_voos.add((no_serie, hora_partida))
        used_voos.add((no_serie, hora_chegada))
        used_chegada.add((hora_chegada, origem, destino))
        used_partida_combo.add((hora_partida, origem, destino))

        print_sql(f"INSERT INTO voo ( no_serie, hora_partida, hora_chegada, partida, chegada) "
                  f"VALUES ( '{no_serie}', '{hora_partida}', '{hora_chegada}', '{origem}', '{destino}');")
        voos.append((voo_id, no_serie))
        voos_dia.append((origem, destino))
        voo_id += 1
        voos_gerados_hoje += 1

        # Atualizar aeroporto atual do avião
        aviao_estado[no_serie] = destino

    # Guardar todos os voos do dia para garantir o inverso
    for origem, destino in voos_dia:
        voos_ida.add((origem, destino, current_time.date()))
        voos_volta_necessarios.add((destino, origem, current_time.date()))
    current_time += timedelta(days=1)
print_sql()

# Gerar voos inversos que não existam ainda (pode ser qualquer avião, qualquer hora)
print_sql("-- === 4b. Voos Inversos ===")
for origem, destino, data in voos_volta_necessarios:
    # Só gera se cidades forem diferentes
    if (origem, destino, data) not in voos_ida and aeroporto_cidade[origem] != aeroporto_cidade[destino]:
        # Escolher avião aleatório
        no_serie = random.choice([a[0] for a in avioes])
        hora_partida = datetime.combine(data, datetime.min.time()) + timedelta(hours=random.randint(5, 22))
        duracao = timedelta(hours=random.randint(1, 4))
        hora_chegada = hora_partida + duracao

        # Garantir unicidade
        tentativas = 0
        while (
            (no_serie, hora_partida) in used_voos or
            (no_serie, hora_chegada) in used_voos or
            (hora_chegada, origem, destino) in used_chegada or
            (hora_partida, origem, destino) in used_partida_combo
        ):
            hora_partida = datetime.combine(data, datetime.min.time()) + timedelta(hours=random.randint(5, 22))
            duracao = timedelta(hours=random.randint(1, 4))
            hora_chegada = hora_partida + duracao
            tentativas += 1
            if tentativas > 20:
                break

        if tentativas > 20:
            continue

        used_voos.add((no_serie, hora_partida))
        used_voos.add((no_serie, hora_chegada))
        used_chegada.add((hora_chegada, origem, destino))
        used_partida_combo.add((hora_partida, origem, destino))

        print_sql(f"INSERT INTO voo ( no_serie, hora_partida, hora_chegada, partida, chegada) "
                  f"VALUES ( '{no_serie}', '{hora_partida}', '{hora_chegada}', '{origem}', '{destino}');")
        voos.append((voo_id, no_serie))
        voo_id += 1
print_sql()

# --- 5. Vendas ---
print_sql("-- === 5. Vendas ===")
# Garantir pelo menos 10.000 vendas
n_vendas = max(int(n_bilhetes / 1.5), 10000)
vendas = []
for venda_id in range(1, n_vendas + 1):
    nif = ''.join(random.choices(string.digits, k=9))
    balcao = random.choice(aeroportos)[0]
    dia = start_date + timedelta(days=random.randint(0, (end_date - start_date).days))
    hora = timedelta(hours=random.randint(0, 23), minutes=random.randint(0, 59), seconds=random.randint(0, 59))
    data_hora = dia + hora
    data_hora_str = data_hora.strftime('%Y-%m-%d %H:%M:%S')
    vendas.append((venda_id, data_hora))
    print_sql(f"INSERT INTO venda ( nif_cliente, balcao, hora) VALUES ( '{nif}', '{balcao}', '{data_hora_str}');")
print_sql()

# --- 6. Bilhetes ---
print_sql("-- === 6. Bilhetes ===")
bilhete_unicos = set()
assentos_por_voo = {}
bilhetes_por_voo = {}

for voo_id, no_serie in voos:
    assentos = [f"{f}{c}" for f in range(1, 31) for c in "ABCDEF"]
    random.shuffle(assentos)
    assentos_por_voo[(voo_id, no_serie)] = assentos
    bilhetes_por_voo[voo_id] = {"prim": 0, "econ": 0}

# Garantir que todos os voos têm pelo menos um bilhete de cada classe
bilhete_id = 1
for voo_id, no_serie in voos:
    for prim in [True, False]:
        nome = random.choice(nomes)
        venda_id = random.randint(1, n_vendas)
        preco = round(random.uniform(50, 500), 2)
        tentativas = 0
        while (voo_id, venda_id, nome) in bilhete_unicos and tentativas < 10:
            venda_id = random.randint(1, n_vendas)
            nome = random.choice(nomes)
            tentativas += 1
        if (voo_id, venda_id, nome) in bilhete_unicos:
            continue
        bilhete_unicos.add((voo_id, venda_id, nome))
        assentos = assentos_por_voo[(voo_id, no_serie)]
        checkin = vendas[venda_id-1][1] < datetime.now()
        if checkin:
            if prim:
                assentos_prim = [a for a in assentos if int(a[:-1]) <= 3]
                if not assentos_prim:
                    continue
                assento = assentos_prim.pop()
                assentos.remove(assento)
                bilhetes_por_voo[voo_id]["prim"] += 1
            else:
                assentos_econ = [a for a in assentos if int(a[:-1]) > 3]
                if not assentos_econ:
                    continue
                assento = assentos_econ.pop()
                assentos.remove(assento)
                bilhetes_por_voo[voo_id]["econ"] += 1
            assento_str = f"'{assento}'"
        else:
            assento_str = "NULL"
        print_sql(f"INSERT INTO bilhete ( voo_id, codigo_reserva, nome_passegeiro, preco, prim_classe, lugar, no_serie) "
                  f"VALUES ( {voo_id}, {venda_id}, '{nome}', {preco}, {str(prim).upper()}, {assento_str}, '{no_serie}');")
        bilhete_id += 1

# Gerar os restantes bilhetes
while bilhete_id <= n_bilhetes:
    voo_id, no_serie = random.choice(voos)
    venda_id = random.randint(1, n_vendas)
    nome = random.choice(nomes)
    preco = round(random.uniform(50, 500), 2)
    prim = random.random() < 0.2
    tentativas = 0
    while (voo_id, venda_id, nome) in bilhete_unicos and tentativas < 10:
        venda_id = random.randint(1, n_vendas)
        nome = random.choice(nomes)
        tentativas += 1
    if (voo_id, venda_id, nome) in bilhete_unicos:
        continue
    bilhete_unicos.add((voo_id, venda_id, nome))
    assentos = assentos_por_voo[(voo_id, no_serie)]
    checkin = vendas[venda_id-1][1] < datetime.now()
    if checkin:
        if prim:
            assentos_prim = [a for a in assentos if int(a[:-1]) <= 3]
            if not assentos_prim:
                continue
            assento = assentos_prim.pop()
            assentos.remove(assento)
            bilhetes_por_voo[voo_id]["prim"] += 1
        else:
            assentos_econ = [a for a in assentos if int(a[:-1]) > 3]
            if not assentos_econ:
                continue
            assento = assentos_econ.pop()
            assentos.remove(assento)
            bilhetes_por_voo[voo_id]["econ"] += 1
        assento_str = f"'{assento}'"
    else:
        assento_str = "NULL"
    print_sql(f"INSERT INTO bilhete (voo_id, codigo_reserva, nome_passegeiro, preco, prim_classe, lugar, no_serie) "
              f"VALUES ({voo_id}, {venda_id}, '{nome}', {preco}, {str(prim).upper()}, {assento_str}, '{no_serie}');")
    bilhete_id += 1
print_sql()