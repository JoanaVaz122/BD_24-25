#!/usr/bin/python3
# Copyright (c) BDist Development Team
# Distributed under the terms of the Modified BSD License.
import os
from logging.config import dictConfig

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

# Use the DATABASE_URL environment variable if it exists, otherwise use the default.
# Use the format postgres://username:password@hostname/database_name to connect to the database.
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


def is_decimal(s):
    """Returns True if string is a parseable float number."""
    try:
        float(s)
        return True
    except ValueError:
        return False


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
            log.debug(f"Found {cur.rowcount} rows.")

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
            log.debug(f"Found {cur.rowcount} rows.")
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
            log.debug(f"Found {cur.rowcount} rows.")

    if not voos:
        return jsonify({"message": "No flights found.", "status": "error"}), 404

    return jsonify(voos), 200




@app.route("/compra/<voo>",methods=("POST",))
def fazer_compra(voo):
    """Update the account balance."""   

    #voo = request.args.get("voo")

    nif_cliente = request.form.get("nif_cliente")
    if len(nif_cliente) != 9 or not nif_cliente.isdigit():
        return jsonify({"message": "NIF must be a 9-digit number.", "status": "error"}), 400
    
    nome_passegeiro = request.form.get("nome_passageiro")
    if not nome_passegeiro:
        return jsonify({"message": "Passenger name is required.", "status": "error"}), 400

    classe_bilhete = request.form.get("prim_classe")
    if classe_bilhete not in ["TRUE", "FALSE"]:
        return jsonify({"message": "Invalid class. Must be TRUE or FALSE.", "status": "error"}), 400

    dados_passageiro = (nome_passegeiro, classe_bilhete)


    error = None

    if not balance:
        error = "Balance is required."
    if not is_decimal(balance):
        error = "Balance is required to be decimal."

    if error is not None:
        return jsonify({"message": error, "status": "error"}), 400
    else:
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE account
                    SET balance = %(balance)s
                    WHERE account_number = %(account_number)s;
                    """,
                    {"account_number": account_number, "balance": balance},
                )
                # The result of this statement is persisted immediately by the database
                # because the connection is in autocommit mode.
                log.debug(f"Updated {cur.rowcount} rows.")

                if cur.rowcount == 0:
                    return (
                        jsonify({"message": "Account not found.", "status": "error"}),
                        404,
                    )

        # The connection is returned to the pool at the end of the `connection()` context but,
        # because it is not in a transaction state, no COMMIT is executed.

        return "", 204


@app.route(
    "/accounts/<account_number>/delete",
    methods=(
        "DELETE",
        "POST",
    ),
)
def account_delete(account_number):
    """Delete the account."""

    with pool.connection() as conn:
        with conn.cursor() as cur:
            try:
                with conn.transaction():
                    # BEGIN is executed, a transaction started
                    cur.execute(
                        """
                        DELETE FROM depositor
                        WHERE account_number = %(account_number)s;
                        """,
                        {"account_number": account_number},
                    )
                    cur.execute(
                        """
                        DELETE FROM account
                        WHERE account_number = %(account_number)s;
                        """,
                        {"account_number": account_number},
                    )
                    # These two operations run atomically in the same transaction
            except Exception as e:
                return jsonify({"message": str(e), "status": "error"}), 500
            else:
                # COMMIT is executed at the end of the block.
                # The connection is in idle state again.
                log.debug(f"Deleted {cur.rowcount} rows.")

                if cur.rowcount == 0:
                    return (
                        jsonify({"message": "Account not found.", "status": "error"}),
                        404,
                    )

    # The connection is returned to the pool at the end of the `connection()` context

    return "", 204


@app.route("/ping", methods=("GET",))
@limiter.exempt
def ping():
    log.debug("ping!")
    return jsonify({"message": "pong!", "status": "success"})


if __name__ == "__main__":
    app.run()
