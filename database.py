import aiosqlite
import time
from pathlib import Path

DB_PATH = Path("trades.db")

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id TEXT PRIMARY KEY,
                asset TEXT,
                direction TEXT,
                amount REAL,
                duration INTEGER,
                timestamp REAL,
                status TEXT,
                result TEXT,
                profit REAL,
                balance_after REAL
            )
        """)
        await db.commit()

async def log_trade(trade_data):
    """
    Log a new trade or update an existing one.
    trade_data: dict containing trade details
    """
    async with aiosqlite.connect(DB_PATH) as db:
        # Check if trade exists
        cursor = await db.execute("SELECT id FROM trades WHERE id = ?", (trade_data['id'],))
        exists = await cursor.fetchone()
        
        if exists:
            # Update existing trade (e.g., adding result)
            await db.execute("""
                UPDATE trades 
                SET result = ?, profit = ?, balance_after = ?, status = ?
                WHERE id = ?
            """, (
                trade_data.get('result'),
                trade_data.get('profit', 0),
                trade_data.get('balance_after'),
                trade_data.get('status', 'completed'),
                trade_data['id']
            ))
        else:
            # Insert new trade
            await db.execute("""
                INSERT INTO trades (id, asset, direction, amount, duration, timestamp, status, result, profit, balance_after)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trade_data['id'],
                trade_data['asset'],
                trade_data['direction'],
                trade_data['amount'],
                trade_data['duration'],
                trade_data.get('timestamp', time.time()),
                trade_data.get('status', 'open'),
                trade_data.get('result', 'pending'),
                trade_data.get('profit', 0),
                trade_data.get('balance_after', 0)
            ))
        await db.commit()

async def get_recent_trades(limit=50):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM trades ORDER BY timestamp DESC LIMIT ?", (limit,))
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

async def get_stats():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT 
                COUNT(*) as total_trades,
                SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN result = 'LOSS' THEN 1 ELSE 0 END) as losses,
                SUM(profit) as total_profit
            FROM trades
            WHERE status = 'completed'
        """)
        row = await cursor.fetchone()
        
        total = row[0] or 0
        wins = row[1] or 0
        losses = row[2] or 0
        profit = row[3] or 0.0
        
        win_rate = (wins / total * 100) if total > 0 else 0
        
        return {
            "total_trades": total,
            "wins": wins,
            "losses": losses,
            "win_rate": round(win_rate, 2),
            "total_profit": round(profit, 2)
        }
