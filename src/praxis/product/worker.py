import argparse
import logging
import os
import time
from praxis.product.storage import ProductStore


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    store = ProductStore(os.environ["PRAXIS_DATABASE_URL"])
    if not store.ready(): raise RuntimeError("Database migrations required")
    while True:
        try: delivered = store.drain_one()
        except Exception:
            # Avoid logging connection strings, payloads or provider credentials.
            logging.error("Outbox transaction failed; retrying")
            if args.once: raise
            time.sleep(2); continue
        if args.once: break
        if not delivered: time.sleep(1)


if __name__ == "__main__": main()
