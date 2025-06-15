#!/usr/bin/python3
import os
from logging.config import dictConfig
import random

from flask import Flask, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from psycopg.rows import namedtuple_row
from psycopg_pool import ConnectionPool
from datetime import datetime, timedelta

dictConfig(
    {
        "version": 1,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] %(levelname)s in %(module)s:%(lineno)s - %(funcName)20s(): %(message)s",
            }
        },
        "handlers": {
            "wsgi": {
                "class": "logging.StreamHandler",
                "stream": "ext://flask.logging.wsgi_errors_stream",
                "formatter": "default",
            }
        },
        "root": {"level": "INFO", "handlers": ["wsgi"]},
    }
)

RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")

app = Flask(__name__)
app.config.from_prefixed_env()
log = app.logger
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=RATELIMIT_STORAGE_URI,
)

DATABASE_URL = os.environ.get("DATABASE_URL", "postgres://aviacao1:aviacao1@postgres/aviacao1")

pool = ConnectionPool(
    conninfo=DATABASE_URL,
    kwargs={
        "autocommit": True,  # If True don’t start transactions automatically.
        "row_factory": namedtuple_row,
    },
    min_size=4,
    max_size=10,
    open=True,
    # check=ConnectionPool.check_connection,
    name="postgres_pool",
    timeout=5,
)

@app.route("/", methods=("GET",))
def list_aeroportos():
    """Show all the aeroports (name and city)."""

    with pool.connection() as conn:
        with conn.cursor() as cur:
            aeroporto = cur.execute(
                """
                SELECT nome, cidade
                FROM aeroporto
                """,
                {},
            ).fetchall()

    return jsonify(aeroporto), 200

@app.route("/voos/<partida>", methods=("GET",))
def lista_voo(partida):
    """Show all the voo, most recent first."""

    with pool.connection() as conn:
        with conn.cursor() as cur:
            now = datetime.now()
            later = now + timedelta(hours=12)

            voos = cur.execute(
                """
                SELECT no_serie, hora_partida, chegada
                FROM voo
                WHERE partida = %(partida)s
                  AND hora_partida BETWEEN %(now)s AND %(later)s
                ORDER BY hora_partida;
                """,
                {"partida": partida, "now": now, "later": later},
            ).fetchall()
        if voos is None:
            return jsonify({"message": "voo not found.", "status": "error"}), 404

    return jsonify(voos), 200

@app.route("/voos/<partida>/<chegada>", methods=("GET",))
def list_flights(partida, chegada):
    """Show the next three available flights from partida to chegada."""

    with pool.connection() as conn:
        with conn.cursor() as cur:
            now = datetime.now()

            voos = cur.execute(
                """
                SELECT v.no_serie, v.hora_partida
                FROM voo v
                WHERE v.partida = %(partida)s
                  AND v.chegada = %(chegada)s
                  AND v.hora_partida > %(now)s
                  AND EXISTS (
                      SELECT 1
                      FROM bilhete b
                      WHERE b.voo_id = v.id
                        AND b.preco IS NOT NULL
                  )
                ORDER BY v.hora_partida
                LIMIT 3;
                """,
                {"partida": partida, "chegada": chegada, "now": now},
            ).fetchall()

            if not voos:
                return jsonify({"message": "No flights found.", "status": "error"}), 404

    return jsonify(voos), 200

@app.route("/compra/<voo>", methods=("POST",))
def compra(voo):
    """populate database with new ticket and sell"""

    with pool.connection() as conn:
        with conn.cursor() as cur:
            with conn.transaction():
                cur.execute(
                    """
                    SELECT id, no_serie, hora_partida
                    FROM  voo
                    WHERE id = %(voo)s
                    """,
                    {"voo": voo}
                )
                lista = cur.fetchone()
                if lista is None:
                    return jsonify({"error": "Voo nao existe"}), 404

                voo_id, voo_nserie, voo_data_partida = lista

                agora = datetime.now()
                date_obj = voo_data_partida
                if date_obj < agora:
                    return jsonify({"error": "Voo ja partiu"}), 400

                agora_str = agora.strftime("%Y-%m-%d %H:%M:%S")

                nif_cliente = request.json['nif']
                if len(nif_cliente) != 9:
                   return jsonify({"error": "Nif tem que ter 9 numeros"}), 400

                cur.execute(
                    """
                    INSERT into venda (nif_cliente, balcao, hora)
                    VALUES (%(nif_cliente)s, %(balcao)s, %(hora)s)
                    RETURNING codigo_reserva
                    """,
                    {"nif_cliente": nif_cliente, "balcao": None, "hora": agora_str},
                )
                codigo_reserva = cur.fetchone()[0]

                ticket_pairs = request.json['ticket-pairs']
                
                if not ticket_pairs:
                    return jsonify({"error": "Lista de passageiros vazia"}), 400

                for (nome_passegeiro, primeira_classe) in ticket_pairs.items():

                    if (not isinstance(nome_passegeiro, str) or
                        not isinstance(primeira_classe, bool)):
                        return jsonify({"error": "Dados de passageiros invalidos"}), 400

                    preco = random.randint(50, 500)
                    cur.execute(
                        """
                        INSERT into bilhete (voo_id, codigo_reserva, nome_passegeiro, preco, prim_classe, lugar, no_serie)
                        VALUES (%(voo_id)s, %(codigo_reserva)s, %(nome_passegeiro)s, %(preco)s, %(prim_classe)s, %(lugar)s, %(voo_nserie)s)
                        """,
                        {"voo_id": voo_id, "codigo_reserva": codigo_reserva, "nome_passegeiro": nome_passegeiro, "preco": preco, "prim_classe": primeira_classe, "lugar": None, "voo_nserie":voo_nserie},
                    )
                
    return jsonify(
        {
            "message": f"Compra realizada com sucesso para o voo.",
            "status": "success",
        }
    ), 201


@app.route("/checkin/<bilhete>", methods=("POST",))
def checkin(bilhete):
    """atribui um assento ao bilhete"""

    with pool.connection() as conn:
        with conn.cursor() as cur:
            with conn.transaction():
                cur.execute(
                    """
                    SELECT voo_id, prim_classe, no_serie
                    FROM bilhete 
                    WHERE id = %(bilhete)s AND lugar IS NULL
                    """,
                    {"bilhete": bilhete}
                )
                linha = cur.fetchone()
                
                if not linha:
                    return jsonify({"error": "Bilhete não existe ou ja foi checked-in"}), 404

                voo_id, prim_classe, no_serie = linha
                
                cur.execute(
                    """
                    SELECT lugar FROM assento
                    WHERE no_serie = %(no_serie)s AND prim_classe = %(prim_classe)s
                    AND (lugar, no_serie)  NOT IN (
                        SELECT lugar, no_serie
                        FROM bilhete
                        WHERE voo_id = %(voo_id)s AND lugar IS NOT NULL)
                    ORDER BY lugar 
                    LIMIT 1
                    """,
                    {"no_serie": no_serie, "prim_classe": prim_classe, "voo_id": voo_id}
                )
                assento_livre = cur.fetchone()
                if not assento_livre:
                    return jsonify({"error": "Não há lugares disponíveis"}), 404

                cur.execute(
                    """
                    UPDATE bilhete
                    SET lugar = %(lugar)s
                    WHERE id = %(bilhete)s
                    """,
                    {"lugar": assento_livre[0], "bilhete": bilhete}
                )

    return jsonify({"message": "Check-in realizado com sucesso", "status": "success"}), 200

if __name__ == "__main__":
    app.run()