"""Run with: uvicorn main:app --reload after installing tbc-payments[fastapi]."""

from __future__ import annotations

import os
import sqlite3
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import RedirectResponse

from tbc_payments import AsyncTBCClient
from tbc_payments.integrations.fastapi import payment_id_from_request


def init_db():
    """Initialize a simple SQLite database for orders."""
    with sqlite3.connect("orders.db") as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tbc_payment_id TEXT,
                paid_at TIMESTAMP
            )
            """
        )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    # Initialize the local database
    init_db()
    
    # Share one AsyncTBCClient through lifespan instead of opening one per request
    tbc = AsyncTBCClient(
        os.environ.get("TBC_API_KEY", "dummy_key"),
        os.environ.get("TBC_CLIENT_ID", "dummy_client_id"),
        os.environ.get("TBC_CLIENT_SECRET", "dummy_secret"),
    )
    app.state.tbc = tbc
    yield
    await tbc.close()


app = FastAPI(lifespan=lifespan)


@app.post("/checkout")
async def checkout(request: Request):
    """Creates a payment and safely redirects the user."""
    tbc: AsyncTBCClient = request.app.state.tbc
    
    # 1. Create a pending order in our local database
    with sqlite3.connect("orders.db") as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO orders (tbc_payment_id) VALUES (NULL)")
        order_id = cursor.lastrowid

    # 2. Create the payment in TBC
    payment = await tbc.create_payment(
        amount={"currency": "GEL", "total": 10},
        return_url=f"http://localhost:8000/orders/{order_id}",
    )

    # 3. Update the order with the actual TBC payment ID
    with sqlite3.connect("orders.db") as conn:
        conn.execute(
            "UPDATE orders SET tbc_payment_id = ? WHERE id = ?",
            (payment.pay_id, order_id)
        )

    # 4. Redirect the user to the checkout page
    return RedirectResponse(url=payment.links.redirect, status_code=303)


@app.post("/webhooks/tbc")
async def tbc_callback(request: Request) -> Response:
    """Handles the callback securely by verifying the status server-side."""
    payment_id = await payment_id_from_request(request)
    tbc: AsyncTBCClient = request.app.state.tbc
    
    # Verify payment status server-side rather than trusting callback data
    payment = await tbc.get_payment(payment_id)
    
    if payment.status == "Succeeded":
        with sqlite3.connect("orders.db") as conn:
            # Idempotency boundary: mark the order paid only if paid_at is NULL
            conn.execute(
                "UPDATE orders SET paid_at = CURRENT_TIMESTAMP WHERE tbc_payment_id = ? AND paid_at IS NULL",
                (payment.pay_id,)
            )
            
    return Response(status_code=200)


@app.get("/orders/{order_id}")
async def get_order(order_id: int):
    """The return page to check the order status."""
    with sqlite3.connect("orders.db") as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Order not found")
            
        return dict(row)