import multiprocessing

bind = "0.0.0.0:8000"
workers = max(multiprocessing.cpu_count() * 2 + 1, 3)
worker_class = "sync"
timeout = 120
graceful_timeout = 30
keepalive = 5
accesslog = "-"
errorlog = "-"
