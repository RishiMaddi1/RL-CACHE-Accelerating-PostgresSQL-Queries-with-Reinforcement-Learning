import psycopg2
import random
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
import redis
from decimal import Decimal
import pickle

# === Redis Setup ===
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)
redis_client.flushdb()


MEMORY_CACHE_SIZE = 50
REDIS_CACHE_SIZE = 100
TOTAL_USERS = 5000
TOTAL_PRODUCTS = 1000
TOTAL_ORDERS = 50000
TOTAL_REVIEWS = 10000
TOTAL_QUERIES = 1000

# === Local PostgreSQL Setup ===

# === Multi-level RL-based Cache Simulation (with real Redis) ===

class MultiLevelRLCache:
    def __init__(self, mem_capacity, redis_capacity, redis_client, alpha=0.3, gamma=0.9, epsilon=0.05, decay_rate=0.75):
        self.mem_capacity = mem_capacity
        self.redis_capacity = redis_capacity
        self.memory_cache = {}
        self.memory_queue = deque()
        self.q_table = defaultdict(lambda: defaultdict(float))
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.decay_rate = decay_rate
        self.freshness = {}
        self.costs = {}
        self.values = defaultdict(int)
        self.redis_client = redis_client

    def decay_q_table(self):
        for state in self.q_table:
            for action in self.q_table[state]:
                self.q_table[state][action] *= self.decay_rate

    def get(self, key):
        now = time.time()
        self.values[key] += 1
        self.freshness[key] = now
        
        if random.uniform(0, 1) < self.epsilon:
            action = random.choice(["evict", "cache"])
        else:
            action = "evict" if self.q_table[key]["evict"] > self.q_table[key]["cache"] else "cache"
        
        # Check memory cache first
        if action == "cache" and key in self.memory_cache:
            return self.memory_cache[key], 'memory'
        
        # Check Redis cache
        if action == "cache":
            redis_key = repr(key)
            value = self.redis_client.get(redis_key)
            if value is not None:
                value = pickle.loads(value)
                # Only promote to memory if it's frequently accessed
                if self.values[key] > 5:  # Example threshold
                    self.put(key, value, promote_from_redis=True)
                return value, 'redis'
        
        return None, None

    def put(self, key, value, promote_from_redis=False):
        if key not in self.memory_cache:
            if len(self.memory_cache) >= self.mem_capacity:
                min_key = min(self.memory_cache, key=lambda k: (self.q_table[k]["cache"], self.freshness.get(k, 0)))
                self.memory_cache.pop(min_key)
                self.memory_queue.remove(min_key)
            self.memory_cache[key] = value
            self.memory_queue.append(key)
        if not promote_from_redis:
            redis_key = repr(key)
            if self.redis_client.dbsize() >= self.redis_capacity:
                all_keys = list(self.redis_client.keys())
                if all_keys:
                    self.redis_client.delete(all_keys[0])
            self.redis_client.set(redis_key, pickle.dumps(value))

    def update_q_value(self, key, action, reward):
        # More aggressive RL: higher reward for memory/redis, penalty for DB
        self.q_table[key][action] += self.alpha * (reward - self.q_table[key][action])

# === Query Definitions ===
queries = [
    ("daily_sales_product", """
        SELECT order_date, SUM(quantity) FROM orders
        WHERE product_id = %s AND order_date > CURRENT_DATE - INTERVAL '30 days'
        GROUP BY order_date ORDER BY order_date;
    """, lambda: (random.randint(1, 20),)),
    # Real-world: Daily sales tracking for specific products
    # Skew: Temporal skew - recent 30 days get more queries
    # Use case: Product managers monitoring daily sales trends

    ("avg_order_value_user", """
        SELECT AVG(p.price * o.quantity) FROM orders o
        JOIN products p ON o.product_id = p.id
        WHERE o.user_id = %s;
    """, lambda: (random.randint(1, 100),)),
    # Real-world: Customer value analysis
    # Skew: User skew - frequent customers get more queries
    # Use case: Marketing team analyzing customer spending patterns

    ("users_also_bought", """
        SELECT DISTINCT o2.product_id FROM orders o1
        JOIN orders o2 ON o1.user_id = o2.user_id AND o1.product_id != o2.product_id
        WHERE o1.product_id = %s LIMIT 5;
    """, lambda: (random.randint(1, 20),)),
    # Real-world: Product recommendation system
    # Skew: Product skew - popular products get more queries
    # Use case: "Customers who bought this also bought..." feature

    ("running_total_sales_product", """
        SELECT order_date, SUM(quantity) OVER (ORDER BY order_date) FROM orders
        WHERE product_id = %s AND order_date > CURRENT_DATE - INTERVAL '30 days'
        ORDER BY order_date;
    """, lambda: (random.randint(1, 20),)),
    # Real-world: Cumulative sales tracking
    # Skew: Temporal skew - recent dates get more queries
    # Use case: Sales team monitoring product performance trends

    ("top_rated_products_category", """
        SELECT name, rating FROM products
        WHERE category = %s ORDER BY rating DESC LIMIT 5;
    """, lambda: (random.choice(['Laptops', 'Mobiles', 'Tablets', 'Accessories', 'Desktops', 'Wearables']),)),
    # Real-world: Category performance analysis
    # Skew: Category skew - popular categories get more queries
    # Use case: Product discovery and category pages

    ("reviewed_and_bought", """
        SELECT DISTINCT u.id, u.name FROM users u
        WHERE u.id IN (SELECT user_id FROM reviews WHERE product_id = %s)
        AND u.id IN (SELECT user_id FROM orders WHERE product_id = %s);
    """, lambda: (pid := random.randint(1, 20), pid)),
    # Real-world: Customer engagement analysis
    # Skew: Product skew - popular products get more queries
    # Use case: Identifying engaged customers for marketing

    ("products_on_promotion_season", """
        SELECT p.* FROM products p
        JOIN promotions pr ON p.id = pr.product_id
        JOIN seasons s ON pr.season_id = s.id
        WHERE s.name = %s;
    """, lambda: (random.choice(['College Start', 'Holiday Sale', 'Back to School', 'Summer Sale', 'New Year']),)),
    # Real-world: Seasonal promotion management
    # Skew: Temporal skew - current season gets more queries
    # Use case: Marketing team managing seasonal promotions

    ("orders_by_city_in_season", """
        SELECT o.* FROM orders o
        JOIN users u ON o.user_id = u.id
        JOIN seasons s ON o.order_date BETWEEN s.start_date AND s.end_date
        WHERE u.city = %s AND s.name = %s;
    """, lambda: (random.choice(['New York', 'London', 'Tokyo', 'Delhi', 'Berlin']), random.choice(['College Start', 'Holiday Sale', 'Back to School', 'Summer Sale', 'New Year']))),
    # Real-world: Geographic sales analysis
    # Skew: Geographic skew - major cities get more queries
    # Use case: Regional sales analysis during specific seasons
]

def synthetic_query_distribution():
    # 1. Burst Detection (10% chance)
    burst = random.random() < 0.1
    if burst:
        # Simulate different types of bursts
        burst_type = random.choice([
            "product_burst",    # Multiple products
            "category_burst",   # All products in a category
            "seasonal_burst"    # Products in a season
        ])
        
        if burst_type == "product_burst":
            # Simulate burst affecting multiple products
            burst_products = random.sample(range(1, 21), 3)  # Random 3 products
            return queries[0], (random.choice(burst_products),)  # daily_sales_product
        elif burst_type == "category_burst":
            # Simulate burst in a popular category
            return queries[4], (random.choice(['Laptops', 'Mobiles', 'Tablets']),)  # top_rated_products_category
        else:  # seasonal_burst
            # Simulate burst during a major sale
            return queries[6], (random.choice(['Holiday Sale', 'Back to School']),)  # products_on_promotion_season
    
    # 2. Hot Query Detection (60% chance)
    hot = random.random() < 0.6
    if hot:
        # Weighted random choice of queries
        q = random.choices(queries, weights=[0.4,0.1,0.1,0.1,0.1,0.05,0.1,0.05])[0]
        
        # Special handling for specific queries
        if q[0] == "daily_sales_product":
            return q, (random.choice([1,2,3]),)  # Only products 1,2,3
        if q[0] == "products_on_promotion_season":
            return q, ("College Start",)  # Only College Start season
        if q[0] == "orders_by_city_in_season":
            return q, ("Delhi", "College Start")  # Only Delhi in College Start
        return q, q[2]()  # Use default parameter generator
    
    # 3. Cold Query (30% chance)
    q = random.choice(queries)  # Equal probability for all queries
    return q, q[2]()  # Use default parameter generator

def run_simulation(with_cache=True, log_queue=None, plot_queue=None):
    conn = psycopg2.connect(
        dbname='postgres',
        user='*******,
        password='*****',
        host='***********',
        port=5432
    )
    cur = conn.cursor()
    query_stats = {q[0]: [] for q in queries}
    mem_hits = 0
    redis_hits = 0
    db_hits = 0
    if with_cache:
        cache = MultiLevelRLCache(MEMORY_CACHE_SIZE, REDIS_CACHE_SIZE, redis_client)
        sim_label = 'With RL-based Multi-level Cache (Supabase PostgreSQL + Redis)'
    else:
        sim_label = 'Without Cache (Baseline, Supabase PostgreSQL)'
    for i in range(TOTAL_QUERIES):
        q, param = synthetic_query_distribution()
        q_name, q_text, _ = q
        cache_key = (q_name,) + tuple(param)
        start = time.time()
        if with_cache:
            cached_result, cache_level = cache.get(cache_key)
            if cached_result:
                result = cached_result
                if cache_level == 'memory':
                    mem_hits += 1
                    reward = 7
                elif cache_level == 'redis':
                    redis_hits += 1
                    reward = 4
                else:
                    reward = 1
            else:
                cur.execute(q_text, param)
                result = cur.fetchall()
                cache.put(cache_key, result)
                db_hits += 1
                reward = -3
            elapsed_ms = (time.time() - start) * 1000
            cache.costs[cache_key] = elapsed_ms
            cache.update_q_value(cache_key, "cache" if cached_result else "evict", reward)
            cache.decay_q_table()
        else:
            cur.execute(q_text, param)
            result = cur.fetchall()
            elapsed_ms = (time.time() - start) * 1000
            db_hits += 1
        query_stats[q_name].append(elapsed_ms)
        if (i + 1) % 10 == 0:
            last_10 = []
            for ql in query_stats.values():
                last_10.extend(ql[-10:])
            avg_last_10 = sum(last_10) / len(last_10) if last_10 else 0
            log_msg = {
                'step': i+1,
                'avg_time': avg_last_10,
                'mem_hits': mem_hits,
                'redis_hits': redis_hits,
                'db_hits': db_hits,
                'label': sim_label
            }
            if log_queue:
                log_queue.put(log_msg)
            if plot_queue:
                plot_queue.put({'step': i+1, 'avg_time': avg_last_10, 'label': sim_label})
        time.sleep(0.001)
    # Summary
    all_times = sum([sum(times) for times in query_stats.values()])
    avg_time = all_times / TOTAL_QUERIES
    summary = {
        'label': sim_label,
        'total_queries': TOTAL_QUERIES,
        'total_time': all_times,
        'avg_time': avg_time,
        'mem_hits': mem_hits,
        'redis_hits': redis_hits,
        'db_hits': db_hits,
        'per_query': {q_name: {
            'count': len(query_stats[q_name]),
            'avg_time': sum(query_stats[q_name]) / len(query_stats[q_name]) if query_stats[q_name] else 0
        } for q_name in query_stats}
    }
    if log_queue:
        log_queue.put('__done__')
        # Send summary as a string
        summary_str = (
            f"--- {sim_label} ---\n"
            f"Total queries: {TOTAL_QUERIES}\n"
            f"Total time: {all_times:.2f} ms\n"
            f"Average query time: {avg_time:.2f} ms\n"
            f"Memory hits: {mem_hits} | Redis hits: {redis_hits} | DB hits: {db_hits}\n"
        )
        log_queue.put(f'__summary__{summary_str}')
    cur.close()
    conn.close()
    return summary

def format_simulation_summary(summary_cache, summary_nocache):
    lines = []
    lines.append("--- Query Simulation Summary (Local PostgreSQL + Redis) ---\n")
    # With cache
    lines.append(f"{summary_cache['label']}")
    lines.append(f"  Total queries run: {summary_cache['total_queries']}")
    lines.append(f"  Total time taken: {summary_cache['total_time']:.2f} ms")
    lines.append(f"  Average query time: {summary_cache['avg_time']:.2f} ms\n")
    for q_name, stats in summary_cache['per_query'].items():
        lines.append(f"  - {q_name}: {stats['count']} queries, avg time {stats['avg_time']:.2f} ms")
    lines.append("")
    # Without cache
    lines.append(f"{summary_nocache['label']}")
    lines.append(f"  Total queries run: {summary_nocache['total_queries']}")
    lines.append(f"  Total time taken: {summary_nocache['total_time']:.2f} ms")
    lines.append(f"  Average query time: {summary_nocache['avg_time']:.2f} ms\n")
    for q_name, stats in summary_nocache['per_query'].items():
        lines.append(f"  - {q_name}: {stats['count']} queries, avg time {stats['avg_time']:.2f} ms")
    lines.append("")
    # Performance comparison
    time_saved = summary_nocache['total_time'] - summary_cache['total_time']
    percent_improvement = (time_saved / summary_nocache['total_time']) * 100
    speedup_factor = summary_nocache['avg_time'] / summary_cache['avg_time']
    lines.append("--- Performance Comparison (Supabase PostgreSQL + Redis) ---\n")
    lines.append(f"Total time saved: {time_saved:.2f} ms")
    lines.append(f"Overall speedup factor: {speedup_factor:.2f}x faster")
    lines.append(f"Overall performance improvement: {percent_improvement:.2f}% faster on average\n")
    lines.append("Per-query type improvement:")
    for q_name in summary_cache['per_query']:
        cached_avg = summary_cache['per_query'][q_name]['avg_time']
        no_cache_avg = summary_nocache['per_query'].get(q_name, {'avg_time': 0})['avg_time']
        q_time_saved = no_cache_avg - cached_avg
        q_percent_improve = (q_time_saved / no_cache_avg) * 100 if no_cache_avg else 0
        q_speedup_factor = no_cache_avg / cached_avg if cached_avg else 0
        lines.append(f"  - {q_name}:")
        lines.append(f"      Avg time without cache: {no_cache_avg:.2f} ms")
        lines.append(f"      Avg time with cache: {cached_avg:.2f} ms")
        lines.append(f"      Speedup factor: {q_speedup_factor:.2f}x")
        lines.append(f"      Improvement: {q_percent_improve:.2f}%")
    return '\\n'.join(lines)


